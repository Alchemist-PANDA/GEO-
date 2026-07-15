import streamlit as st

from geo_audit_agent.ui.access import require_user_or_demo
from geo_audit_agent.ui.theme import apply_theme, render_page_header

st.set_page_config(page_title="Workflow Console", page_icon="◇", layout="wide")
apply_theme()
user = require_user_or_demo()

render_page_header(
    "ORCHESTRATION",
    "Workflow Console",
    "Run a guarded request through context assembly, policy checks, specialist agents, and final inspection.",
)
st.caption("Input guard → context → policy → specialist agent → inspector")

with st.form("agentic_form"):
    user_message = st.text_area(
        "Instruction",
        placeholder="Example: Audit Burger Hub visibility in Islamabad and identify the highest-priority gaps.",
        height=120,
    )
    col1, col2, col3 = st.columns(3)
    brand_name = col1.text_input("Brand name", value=st.session_state.get("brand_name", "Burger Hub"))
    category = col2.text_input("Category", value=st.session_state.get("category", "fast food"))
    city = col3.text_input("Market", value=st.session_state.get("city", "Islamabad"))
    submitted = st.form_submit_button("Run governed workflow", type="primary", use_container_width=True)

if submitted and user_message.strip():
    from geo_audit_agent.orchestration.langgraph_workflow import build_agentic_graph
    from geo_audit_agent.orchestration.state import AgenticState

    state = AgenticState(
        user_message=user_message.strip(),
        brand_name=brand_name.strip(),
        category=category.strip(),
        city=city.strip(),
        user_id=user.id,
    )

    with st.status("Running governed workflow…", expanded=True) as status:
        st.write("Validating request, context, and permissions")
        try:
            result = build_agentic_graph().invoke(state)
            blocked = result.get("blocked", False)
            if blocked:
                status.update(label="Blocked by guardrail or policy", state="error")
                st.error(result.get("block_reason", "This request cannot be completed safely."))
            else:
                status.update(label="Workflow complete", state="complete")

            st.markdown("### Run summary")
            res_col1, res_col2, res_col3 = st.columns(3)
            res_col1.metric("Intent", result.get("intent") or "—")
            res_col2.metric("Policy", "Blocked" if blocked else "Passed")
            inspector = result.get("inspector_verdict", {})
            res_col3.metric("Inspector", "Pass" if inspector.get("passed") else "Review")

            if result.get("copilot_answer"):
                with st.container(border=True):
                    st.markdown("### Copilot response")
                    st.markdown(result["copilot_answer"])

            if result.get("gaps"):
                st.markdown("### Identified gaps")
                for gap in result["gaps"]:
                    severity = gap.get("severity", "Medium")
                    with st.expander(f"{severity} · {gap.get('gap_type', 'Gap')}"):
                        st.write(gap.get("description", ""))

            if result.get("competitor_data"):
                with st.expander("Competitor analysis"):
                    st.json(result["competitor_data"])

            if result.get("action_results"):
                st.markdown("### Action results")
                for action_result in result["action_results"]:
                    status_label = str(action_result.get("status", "unknown")).replace("_", " ").title()
                    with st.expander(f"{action_result.get('action_id', 'action')} · {status_label}"):
                        if action_result.get("artifact"):
                            st.code(str(action_result["artifact"])[:2000])

            with st.expander("Inspector details"):
                st.json(inspector)
            with st.expander("Trace and usage"):
                st.code(result.get("trace_id", ""))
                st.json(
                    {
                        "intent": result.get("intent"),
                        "blocked": blocked,
                        "tokens": result.get("tokens", 0),
                        "cost_usd": result.get("cost_usd", 0.0),
                    }
                )
        except Exception:
            status.update(label="Workflow failed", state="error")
            st.error("The workflow could not be completed. Review the inputs and try again.")
elif submitted:
    st.warning("Enter a clear instruction before running the workflow.")
