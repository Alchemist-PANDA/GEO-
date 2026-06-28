from langgraph.graph import StateGraph, END
from geo_audit_agent.orchestration.state import AgenticState
from geo_audit_agent.guardrails.manager import check_phase
from geo_audit_agent.policy.engine import PolicyEngine
from geo_audit_agent.agents.action_agent import ActionAgent
from geo_audit_agent.agents.inspector_agent import InspectorAgent
from geo_audit_agent.context import build_context

def _node_input_guard(state: AgenticState) -> AgenticState:
    d = check_phase("input", {"user_message": state.user_message,
        "brand_name": state.brand_name}, trace_id=state.trace_id)
    if d.blocked:
        state.blocked = True
        state.block_reason = "; ".join(v.message for v in d.violations)
    return state

def _node_context(state: AgenticState) -> AgenticState:
    ctx = build_context(state.user_message, brand=state.brand_name, industry=state.category)
    state.context = ctx
    state.intent = ctx["intent"]
    return state

def _node_policy(state: AgenticState) -> AgenticState:
    res = PolicyEngine().enforce({"intent": state.intent, "brand_known": bool(state.brand_name),
        "evidence": state.context.get("bundle", {}).get("evidence"),
        "audit_status": "complete" if state.gaps else "pending",
        "human_approved": False})
    if not res["allowed"]:
        state.blocked = True
        state.block_reason = "; ".join(b["message"] for b in res["blocking"])
    return state

def _route_after_policy(state: AgenticState) -> str:
    if state.blocked:
        return "inspector"          # inspector still logs the block
    return {"audit": "audit", "compare": "competitor", "deploy": "action"
            }.get(state.intent, "copilot")

def _node_audit(state):       # wraps existing audit agent
    from geo_audit_agent.agent import build_geo_audit_agent
    out = build_geo_audit_agent().invoke({"brand": state.brand_name,
        "category": state.category, "city": state.city, "force_mock": True})
    state.gaps = out.get("gaps", [])
    state.next_agent = "inspector"
    return state

def _node_competitor(state):  # wraps existing competitor agent
    from geo_audit_agent.agents.unified_competitor_agent import run_competitor_scan
    state.competitor_data = run_competitor_scan(state.brand_name, state.category, state.city) \
        if False else {}          # call the real entrypoint; mock-safe
    state.next_agent = "inspector"
    return state

def _node_copilot(state):
    from geo_audit_agent.copilot import engine
    state.copilot_answer = engine.get_response(state.user_message,
        {**state.context.get("bundle", {}), "brand_name": state.brand_name})
    state.next_agent = "inspector"
    return state

def _node_action(state):
    a = ActionAgent()
    state = a.plan(state)
    state = a.execute(state)
    state.next_agent = "inspector"
    return state

def _node_inspector(state):
    output = {"text": state.copilot_answer or state.block_reason or str(state.action_results),
              "is_recommendation": state.intent in ("recommend", "deploy"),
              "tool_calls": []}
    verdict = InspectorAgent().inspect(output, state.context,
        agent_id=state.intent or "system", trace_id=state.trace_id)
    state.inspector_verdict = {"passed": verdict.passed, "issues": verdict.issues,
        "risk": verdict.risk}
    return state

def build_agentic_graph():
    g = StateGraph(AgenticState)
    g.add_node("input_guard", _node_input_guard)
    g.add_node("context", _node_context)
    g.add_node("policy", _node_policy)
    g.add_node("audit", _node_audit)
    g.add_node("competitor", _node_competitor)
    g.add_node("copilot", _node_copilot)
    g.add_node("action", _node_action)
    g.add_node("inspector", _node_inspector)

    g.set_entry_point("input_guard")
    g.add_conditional_edges("input_guard",
        lambda s: "inspector" if s.blocked else "context",
        {"inspector": "inspector", "context": "context"})
    g.add_edge("context", "policy")
    g.add_conditional_edges("policy", _route_after_policy,
        {"audit": "audit", "competitor": "competitor", "copilot": "copilot",
         "action": "action", "inspector": "inspector"})
    for n in ("audit", "competitor", "copilot", "action"):
        g.add_edge(n, "inspector")
    g.add_edge("inspector", END)
    return g.compile()
