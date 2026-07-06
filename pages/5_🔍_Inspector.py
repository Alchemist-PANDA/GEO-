import streamlit as st

st.set_page_config(page_title="Inspector Dashboard", page_icon="🔍", layout="wide")
if not st.session_state.get("authenticated"):
    st.warning("Please log in from the main dashboard first.")
    st.stop()

st.title("🔍 Inspector Dashboard")

try:
    from geo_audit_agent.db.models import GuardrailViolation, ImprovementProposal, InspectorCheck
    from geo_audit_agent.db.session import get_session

    with get_session() as s:
        recent_checks = s.query(InspectorCheck).order_by(
            InspectorCheck.created_at.desc()).limit(50).all()
        recent_violations = s.query(GuardrailViolation).order_by(
            GuardrailViolation.created_at.desc()).limit(50).all()
        pending_proposals = s.query(ImprovementProposal).filter(
            ImprovementProposal.status == "pending").order_by(
            ImprovementProposal.created_at.desc()).limit(20).all()

    col1, col2, col3 = st.columns(3)
    total_checks = len(recent_checks)
    passed = sum(1 for c in recent_checks if c.passed)
    col1.metric("Inspector Checks", total_checks)
    col2.metric("Pass Rate", f"{(passed/total_checks*100):.0f}%" if total_checks else "N/A")
    col3.metric("Guardrail Violations", len(recent_violations))

    st.subheader("Recent Inspector Results")
    if recent_checks:
        for check in recent_checks[:10]:
            status = "✅" if check.passed else "❌"
            with st.expander(f"{status} {check.agent_id} — {check.check_type} ({check.created_at})"):
                st.json(check.result)
    else:
        st.info("No inspector checks recorded yet.")

    st.subheader("Recent Guardrail Violations")
    if recent_violations:
        for v in recent_violations[:10]:
            severity_color = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(v.severity, "⚪")
            with st.expander(f"{severity_color} {v.guardrail_type} — {v.severity} ({v.created_at})"):
                st.json(v.violation_details)
                if v.blocked:
                    st.error("This violation BLOCKED execution.")
    else:
        st.info("No guardrail violations recorded yet.")

    st.subheader("Pending Improvement Proposals")
    if pending_proposals:
        for p in pending_proposals:
            with st.expander(f"📋 {p.agent_id} — {p.proposal_type}: {p.description[:80]}"):
                st.json(p.payload)
                col_a, col_r = st.columns(2)
                if col_a.button("✅ Approve", key=f"approve_{p.id}"):
                    with get_session() as s2:
                        prop = s2.get(ImprovementProposal, p.id)
                        if prop:
                            prop.status = "approved"
                            s2.add(prop)
                            s2.commit()
                    st.success("Proposal approved.")
                    st.rerun()
                if col_r.button("❌ Reject", key=f"reject_{p.id}"):
                    with get_session() as s2:
                        prop = s2.get(ImprovementProposal, p.id)
                        if prop:
                            prop.status = "rejected"
                            s2.add(prop)
                            s2.commit()
                    st.warning("Proposal rejected.")
                    st.rerun()
    else:
        st.info("No pending improvement proposals.")

except Exception as e:
    st.warning(f"Database not available — Inspector dashboard requires a running database. ({e})")
    st.info("Run `alembic upgrade head` to create the required tables.")
