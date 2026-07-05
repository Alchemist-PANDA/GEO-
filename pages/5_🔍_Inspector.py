import streamlit as st
from sqlmodel import select
from geo_audit_agent.db.session import get_session
from geo_audit_agent.db.models import InspectorCheck, GuardrailViolation, ImprovementProposal

st.set_page_config(page_title="Inspector Dashboard", page_icon="🔍", layout="wide")
st.title("🔍 Inspector Dashboard")

st.markdown("### Recent Inspector Checks")
try:
    with get_session() as s:
        checks = s.exec(select(InspectorCheck).order_by(InspectorCheck.created_at.desc()).limit(10)).all()
        if checks:
            st.dataframe([{
                "Time": c.created_at,
                "Agent": c.agent_id,
                "Passed": c.passed,
                "Risk": c.result.get("risk", "N/A"),
                "Issues": ", ".join(c.result.get("issues", []))
            } for c in checks], use_container_width=True)
        else:
            st.info("No inspector checks recorded yet.")
except Exception as e:
    st.error(f"Could not load Inspector Checks: {e}")

st.markdown("### Guardrail Violations")
try:
    with get_session() as s:
        violations = s.exec(select(GuardrailViolation).order_by(GuardrailViolation.created_at.desc()).limit(10)).all()
        if violations:
            st.dataframe([{
                "Time": v.created_at,
                "Agent": v.agent_id,
                "Type": v.guardrail_type,
                "Severity": v.severity,
                "Blocked": v.blocked
            } for v in violations], use_container_width=True)
        else:
            st.info("No guardrail violations recorded yet.")
except Exception as e:
    st.error(f"Could not load Guardrail Violations: {e}")

st.markdown("### Action Proposals (Self Improvement)")
try:
    with get_session() as s:
        proposals = s.exec(select(ImprovementProposal).where(ImprovementProposal.status == "pending").order_by(ImprovementProposal.created_at.desc()).limit(10)).all()
        if proposals:
            for p in proposals:
                with st.expander(f"Proposal for {p.agent_id}: {p.proposal_type}"):
                    st.write(p.description)
                    st.json(p.payload)
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Approve", key=f"appr_prop_{p.id}"):
                        p.status = "approved"; s.commit(); st.rerun()
                    if c2.button("❌ Reject", key=f"rej_prop_{p.id}"):
                        p.status = "rejected"; s.commit(); st.rerun()
        else:
            st.info("No pending improvement proposals.")
except Exception as e:
    st.error(f"Could not load Improvement Proposals: {e}")
