import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from geo_audit_agent.api.auth import get_current_user
from geo_audit_agent.db.session import get_async_session

router = APIRouter()
logger = logging.getLogger(__name__)


class AgenticRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    brand_name: str = Field(..., min_length=1, max_length=200)
    category: str = ""
    city: str = ""


class AgenticResponse(BaseModel):
    trace_id: str
    intent: str
    blocked: bool
    block_reason: str = ""
    copilot_answer: str = ""
    gaps: list = []
    competitor_data: dict = {}
    action_results: list = []
    inspector_verdict: dict = {}


@router.post("/agentic/run", response_model=AgenticResponse)
async def run_agentic_workflow(
    req: AgenticRequest,
    user_id: str = Depends(get_current_user),
):
    from geo_audit_agent.orchestration.langgraph_workflow import build_agentic_graph
    from geo_audit_agent.orchestration.state import AgenticState

    state = AgenticState(
        user_message=req.message,
        brand_name=req.brand_name,
        category=req.category,
        city=req.city,
        user_id=user_id,
    )

    try:
        graph = build_agentic_graph()
        result = graph.invoke(state)
    except Exception as e:
        logger.exception("Agentic workflow failed: %s", e)
        raise HTTPException(status_code=500, detail="Workflow execution failed") from e

    return AgenticResponse(
        trace_id=result.get("trace_id", ""),
        intent=result.get("intent", ""),
        blocked=result.get("blocked", False),
        block_reason=result.get("block_reason", ""),
        copilot_answer=result.get("copilot_answer", ""),
        gaps=result.get("gaps", []),
        competitor_data=result.get("competitor_data", {}),
        action_results=result.get("action_results", []),
        inspector_verdict=result.get("inspector_verdict", {}),
    )


class GuardrailCheckRequest(BaseModel):
    phase: str = Field(..., pattern="^(input|context|retrieval|memory|tool|agent|business|output|security|cost|workflow|human_approval)$")
    payload: dict


class GuardrailCheckResponse(BaseModel):
    allowed: bool
    violations: list


@router.post("/guardrails/check", response_model=GuardrailCheckResponse)
async def check_guardrails(
    req: GuardrailCheckRequest,
    user_id: str = Depends(get_current_user),
):
    from geo_audit_agent.guardrails.manager import check_phase
    decision = check_phase(req.phase, req.payload)
    return GuardrailCheckResponse(
        allowed=decision.allowed,
        violations=[{"guardrail_type": v.guardrail_type, "rule": v.rule, "severity": v.severity.value,
                      "message": v.message} for v in decision.violations],
    )


class InspectorRequest(BaseModel):
    output: dict
    context: dict = {}
    agent_id: str = "system"


class InspectorResponse(BaseModel):
    passed: bool
    checks: dict
    issues: list
    risk: str


@router.post("/inspector/check", response_model=InspectorResponse)
async def run_inspector(
    req: InspectorRequest,
    user_id: str = Depends(get_current_user),
):
    from geo_audit_agent.agents.inspector_agent import InspectorAgent
    verdict = InspectorAgent().inspect(req.output, req.context, agent_id=req.agent_id)
    return InspectorResponse(
        passed=verdict.passed,
        checks=verdict.checks,
        issues=verdict.issues,
        risk=verdict.risk,
    )


@router.get("/improvement/proposals")
async def list_proposals(
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session),
):
    try:
        from geo_audit_agent.db.models import ImprovementProposal
        proposals = session.query(ImprovementProposal).filter(
            ImprovementProposal.status == "pending"
        ).order_by(ImprovementProposal.created_at.desc()).limit(20).all()
        return [{"id": str(p.id), "agent_id": p.agent_id, "type": p.proposal_type,
                 "description": p.description, "status": p.status} for p in proposals]
    except Exception as e:
        logger.warning("Could not fetch proposals: %s", e)
        return []
