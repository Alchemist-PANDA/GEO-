"""Claude reads winning vs losing traces and proposes ONE scoped change."""
import logging

from geo_audit_agent.llm import gateway

logger = logging.getLogger(__name__)


def propose(agent_id: str, limit: int = 40) -> dict | None:
    try:
        from geo_audit_agent.db.models import AgentTrace
        from geo_audit_agent.db.session import get_session
        with get_session() as s:
            traces = (s.query(AgentTrace).filter(AgentTrace.agent_id == agent_id)
                      .filter(AgentTrace.score.isnot(None))
                      .order_by(AgentTrace.created_at.desc()).limit(limit).all())
    except Exception as e:
        logger.warning("improvement_proposer: failed to load traces: %s", e)
        return None
    if len(traces) < 10:
        return None
    wins = [t for t in traces if (t.score or 0) >= 0.8]
    losses = [t for t in traces if (t.score or 0) < 0.5]
    res = gateway.claude(
        system=("You improve an AI agent. Compare winning vs losing traces and "
                "propose exactly ONE scoped, low-risk change. Return JSON "
                "{\"proposal_type\":\"prompt|ranking|rule|tool\",\"description\":str,"
                "\"payload\":{...}}."),
        user=f"WINS:\n{[t.decision for t in wins][:10]}\n\nLOSSES:\n{[t.decision for t in losses][:10]}",
        force_json=True)
    data = gateway.parse_json(res.text)
    if not data.get("description"):
        return None
    try:
        from geo_audit_agent.db.models import ImprovementProposal
        from geo_audit_agent.db.session import get_session
        from geo_audit_agent.observability.metrics import IMPROVEMENT_PROPOSALS
        IMPROVEMENT_PROPOSALS.labels(agent=agent_id, status="proposed").inc()
        with get_session() as s:
            p = ImprovementProposal(agent_id=agent_id, proposal_type=data.get("proposal_type", "prompt"),
                description=data["description"], payload=data.get("payload", {}), status="pending")
            s.add(p)
            s.commit()
            s.refresh(p)
            return {"id": str(p.id), **data}
    except Exception as e:
        logger.warning("improvement_proposer: failed to persist proposal: %s", e)
        return data
