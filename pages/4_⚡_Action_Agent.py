import streamlit as st

from geo_audit_agent.actions.mapper import map_gaps_to_actions
from geo_audit_agent.agents.action_agent import ActionAgent
from geo_audit_agent.orchestration.state import AgenticState
from geo_audit_agent.ui.access import require_user_or_demo

st.set_page_config(page_title="Action Agent", page_icon="⚡", layout="wide")
user = require_user_or_demo()

st.title("⚡ Action Agent")
st.warning("Planning weights are heuristic prioritization aids, not measured visibility lift forecasts.")
gaps = st.session_state.get("audit_results", {}).get("gaps", [])
if not gaps:
    st.info("Run an audit first — the Action Agent turns gaps into an execution plan.")
    st.stop()

active_audit = st.session_state.get("active_audit") or {}
st.caption(
    f"Selected audit: {active_audit.get('brand_name', 'Unknown brand')} · "
    f"{active_audit.get('city', 'Unknown market')} · {active_audit.get('data_source', 'unavailable').upper()}"
)
if active_audit.get("data_source") == "simulated":
    st.error("DEMO DATA — plans are illustrative and must not be treated as measured provider findings.")

actions = map_gaps_to_actions(gaps)
st.subheader("Proposed Plan (ranked by impact / effort)")
approvals = {}
for a in actions:
    c1, c2, c3, c4 = st.columns([4, 1, 1, 2])
    c1.markdown(f"**{a.title}**  \n_{a.category}_")
    c2.metric("Planning weight", f"{a.impact_pct:.0f}")
    c3.metric("Effort", f"{a.effort_min}m")
    if a.requires_approval:
        approvals[a.id] = c4.checkbox("Approve", key=f"appr_{a.id}")
    else:
        c4.caption("No approval needed")
        approvals[a.id] = True

if st.button("Execute Approved Actions", type="primary"):
    state = AgenticState(brand_name=st.session_state.get("brand_name", ""),
        gaps=gaps, plan_id=None, user_id=user.id)
    state.action_plan = [{"action_id": a.id, "title": a.title, "platform": a.platform,
        "requires_approval": a.requires_approval, "approved": approvals.get(a.id, False)}
        for a in actions]
    state = ActionAgent().execute(state)
    for r in state.action_results:
        icon = {"deployed": "✅", "complete": "✅", "fallback": "📄",
                "awaiting_approval": "⏳"}.get(r["status"], "⚠️")
        with st.expander(f"{icon} {r['action_id']} — {r['status']}"):
            if r.get("artifact"):
                st.code(str(r["artifact"])[:2000])
            if r.get("instructions"):
                st.caption(r["instructions"])
