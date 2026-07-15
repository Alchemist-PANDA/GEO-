import streamlit as st

from geo_audit_agent.actions.mapper import map_gaps_to_actions
from geo_audit_agent.agents.action_agent import ActionAgent
from geo_audit_agent.orchestration.state import AgenticState
from geo_audit_agent.ui.access import require_user_or_demo
from geo_audit_agent.ui.theme import apply_theme, render_empty, render_page_header

st.set_page_config(page_title="Action Agent", page_icon="◆", layout="wide")
apply_theme()
user = require_user_or_demo()

render_page_header("ACTION", "Action Agent", "Turn evidence-backed visibility gaps into a prioritized, approval-gated execution plan.")
st.warning("Planning weights are prioritization aids—not measured visibility-lift forecasts.")

gaps = st.session_state.get("audit_results", {}).get("gaps", [])
if not gaps:
    render_empty("→", "No action plan yet", "Run a visibility audit first. Verified gaps will appear here as a reviewable execution plan.")
    if st.button("Open Audit Studio", type="primary"):
        st.switch_page("pages/1_📈_Audit_Tool.py")
    st.stop()

active_audit = st.session_state.get("active_audit") or {}
st.caption(
    f"Selected audit: {active_audit.get('brand_name', 'Unknown brand')} · "
    f"{active_audit.get('city', 'Unknown market')} · {active_audit.get('data_source', 'unavailable').upper()}"
)
if active_audit.get("data_source") == "simulated":
    st.warning("Demo data: plans are illustrative and must not be treated as measured provider findings.")

actions = map_gaps_to_actions(gaps)
st.markdown("### Recommended sequence")
st.caption("Review each proposed action, inspect the effort, and approve only what your team is ready to execute.")
approvals = {}
for index, action in enumerate(actions, start=1):
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([5, 1.2, 1.2, 1.6])
        c1.markdown(f"#### {index:02d} · {action.title}")
        c1.caption(action.category)
        c2.metric("Weight", f"{action.impact_pct:.0f}")
        c3.metric("Effort", f"{action.effort_min}m")
        if action.requires_approval:
            approvals[action.id] = c4.checkbox("Approve", key=f"appr_{action.id}")
        else:
            c4.success("Pre-approved")
            approvals[action.id] = True

st.divider()
if st.button("Execute approved actions", type="primary", use_container_width=True):
    state = AgenticState(
        brand_name=st.session_state.get("brand_name", ""),
        gaps=gaps,
        plan_id=None,
        user_id=user.id,
    )
    state.action_plan = [
        {
            "action_id": action.id,
            "title": action.title,
            "platform": action.platform,
            "requires_approval": action.requires_approval,
            "approved": approvals.get(action.id, False),
        }
        for action in actions
    ]
    with st.status("Executing approved actions…", expanded=True):
        state = ActionAgent().execute(state)
    for result in state.action_results:
        with st.expander(f"{result['action_id']} · {result['status'].replace('_', ' ').title()}"):
            if result.get("artifact"):
                st.code(str(result["artifact"])[:2000])
            if result.get("instructions"):
                st.caption(result["instructions"])
