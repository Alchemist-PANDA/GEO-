import streamlit as st

st.set_page_config(page_title="Agentic Workflow", page_icon="🧠", layout="wide")
if not st.session_state.get("authenticated"):
    st.warning("Please log in from the main dashboard first.")
    st.stop()

st.title("🧠 Agentic Workflow (LangGraph)")
st.caption("Full multi-agent orchestration: input guard → context → policy → agent → inspector")

with st.form("agentic_form"):
    user_message = st.text_area("What would you like to do?",
        placeholder="e.g. 'Audit Burger Hub visibility in Islamabad' or 'Compare my competitors'",
        height=100)
    col1, col2, col3 = st.columns(3)
    brand_name = col1.text_input("Brand Name", value=st.session_state.get("brand_name", "Burger Hub"))
    category = col2.text_input("Category", value="fast food")
    city = col3.text_input("City", value="Islamabad")
    submitted = st.form_submit_button("Run Agentic Workflow", type="primary", use_container_width=True)

if submitted and user_message.strip():
    from geo_audit_agent.orchestration.langgraph_workflow import build_agentic_graph
    from geo_audit_agent.orchestration.state import AgenticState

    state = AgenticState(
        user_message=user_message.strip(),
        brand_name=brand_name,
        category=category,
        city=city,
    )

    with st.status("Running agentic workflow...", expanded=True) as status:
        st.write("🛡️ Input guardrail check...")
        try:
            graph = build_agentic_graph()
            r = graph.invoke(state)

            blocked = r.get("blocked", False)
            if blocked:
                status.update(label="🚫 Blocked by guardrail/policy", state="error")
                st.error(f"**Blocked:** {r.get('block_reason', 'Unknown')}")
            else:
                status.update(label="✅ Workflow complete", state="complete")

            st.subheader("Results")

            res_col1, res_col2, res_col3 = st.columns(3)
            res_col1.metric("Intent", r.get("intent") or "—")
            res_col2.metric("Blocked", "Yes" if blocked else "No")
            inspector = r.get("inspector_verdict", {})
            verdict_label = "Pass" if inspector.get("passed") else "Fail"
            res_col3.metric("Inspector", verdict_label)

            if r.get("copilot_answer"):
                st.subheader("Copilot Response")
                st.markdown(r["copilot_answer"])

            if r.get("gaps"):
                st.subheader("Identified Gaps")
                for gap in r["gaps"]:
                    severity = gap.get("severity", "Medium")
                    icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(severity, "⚪")
                    with st.expander(f"{icon} {gap.get('gap_type', 'Gap')} — {severity}"):
                        st.write(gap.get("description", ""))

            if r.get("competitor_data"):
                st.subheader("Competitor Analysis")
                st.json(r["competitor_data"])

            if r.get("action_results"):
                st.subheader("Action Results")
                for ar in r["action_results"]:
                    icon = {"deployed": "✅", "complete": "✅", "fallback": "📄",
                            "awaiting_approval": "⏳"}.get(ar.get("status"), "⚠️")
                    with st.expander(f"{icon} {ar.get('action_id', 'action')} — {ar.get('status')}"):
                        if ar.get("artifact"):
                            st.code(str(ar["artifact"])[:2000])

            with st.expander("Inspector Details"):
                st.json(inspector)

            with st.expander("Trace ID & Debug"):
                st.code(r.get("trace_id", ""))
                st.json({"intent": r.get("intent"), "blocked": blocked,
                         "tokens": r.get("tokens", 0), "cost_usd": r.get("cost_usd", 0.0)})

        except Exception as e:
            status.update(label="❌ Workflow Failed", state="error")
            st.error(f"Error: {e}")

elif submitted:
    st.warning("Please enter a message.")
