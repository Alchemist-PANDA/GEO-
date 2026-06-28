import importlib
from geo_audit_agent.actions.mapper import map_gaps_to_actions
from geo_audit_agent.actions import tracker
from geo_audit_agent.guardrails.manager import check_phase
from geo_audit_agent.observability.langfuse_tracer import trace_span

class ActionAgent:
    @trace_span("action.plan", agent_id="action")
    def plan(self, state):
        actions = map_gaps_to_actions(state.gaps)
        state.action_plan = [{"action_id": a.id, "title": a.title,
            "impact_pct": a.impact_pct, "effort_min": a.effort_min,
            "platform": a.platform, "requires_approval": a.requires_approval}
            for a in actions]
        return state

    @trace_span("action.execute", agent_id="action")
    def execute(self, state):
        results = []
        for item in state.action_plan:
            # double gate: human-approval guardrail
            decision = check_phase("human_approval", {"action_id": item["action_id"],
                "human_approved": item.get("approved", False)},
                agent_id="action", trace_id=state.trace_id)
            if decision.blocked:
                results.append({"action_id": item["action_id"], "status": "awaiting_approval"})
                continue
            mod = importlib.import_module(
                f"geo_audit_agent.actions.executors.{_executor_of(item['action_id'])}")
            res = mod.execute(state.action_context())
            res["action_id"] = item["action_id"]
            tracker.record(state.plan_id, item["action_id"], res)
            results.append(res)
        state.action_results = results
        return state

def _executor_of(action_id):
    from geo_audit_agent.actions.registry import REGISTRY
    return REGISTRY[action_id].executor
