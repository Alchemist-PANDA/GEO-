import streamlit as st

from auth import require_admin_user
from geo_audit_agent.ui.theme import apply_theme, render_empty, render_page_header

st.set_page_config(page_title="Quality Inspector", page_icon="◆", layout="wide")
apply_theme()
admin = require_admin_user()

render_page_header(
    "GOVERNANCE",
    "Quality Inspector",
    "Review automated checks, blocked executions, and proposed improvements before they affect production workflows.",
)

try:
    from geo_audit_agent.db.models import GuardrailViolation, ImprovementProposal, InspectorCheck
    from geo_audit_agent.db.session import get_session

    with get_session() as session:
        recent_checks = session.query(InspectorCheck).order_by(InspectorCheck.created_at.desc()).limit(50).all()
        recent_violations = session.query(GuardrailViolation).order_by(
            GuardrailViolation.created_at.desc()
        ).limit(50).all()
        pending_proposals = session.query(ImprovementProposal).filter(
            ImprovementProposal.status == "pending"
        ).order_by(ImprovementProposal.created_at.desc()).limit(20).all()

    col1, col2, col3 = st.columns(3)
    total_checks = len(recent_checks)
    passed = sum(1 for check in recent_checks if check.passed)
    col1.metric("Inspector checks", total_checks)
    col2.metric("Pass rate", f"{(passed / total_checks * 100):.0f}%" if total_checks else "Not available")
    col3.metric("Guardrail violations", len(recent_violations))

    st.markdown("### Recent inspector results")
    if recent_checks:
        for check in recent_checks[:10]:
            status = "Passed" if check.passed else "Failed"
            with st.expander(f"{status} · {check.agent_id} · {check.check_type} · {check.created_at}"):
                st.json(check.result)
    else:
        render_empty("✓", "No checks recorded", "Inspector results will appear here after governed workflows run.")

    st.markdown("### Guardrail events")
    if recent_violations:
        for violation in recent_violations[:10]:
            with st.expander(
                f"{violation.severity.title()} · {violation.guardrail_type} · {violation.created_at}"
            ):
                st.json(violation.violation_details)
                if violation.blocked:
                    st.error("Execution was blocked by this guardrail event.")
    else:
        render_empty("—", "No guardrail events", "No recent policy or safety violations are recorded.")

    st.markdown("### Improvement proposals")
    if pending_proposals:
        for proposal in pending_proposals:
            with st.expander(f"{proposal.agent_id} · {proposal.proposal_type}: {proposal.description[:80]}"):
                st.json(proposal.payload)
                approve_col, reject_col = st.columns(2)
                if approve_col.button("Approve proposal", key=f"approve_{proposal.id}", type="primary"):
                    with get_session() as session:
                        record = session.get(ImprovementProposal, proposal.id)
                        if record:
                            record.status = "approved"
                            session.add(record)
                            session.commit()
                    st.success("Proposal approved.")
                    st.rerun()
                if reject_col.button("Reject proposal", key=f"reject_{proposal.id}"):
                    with get_session() as session:
                        record = session.get(ImprovementProposal, proposal.id)
                        if record:
                            record.status = "rejected"
                            session.add(record)
                            session.commit()
                    st.warning("Proposal rejected.")
                    st.rerun()
    else:
        render_empty("＋", "No proposals awaiting review", "New proposals will remain here until an administrator approves or rejects them.")

except Exception:
    st.error("The governance data service is temporarily unavailable.")
    st.caption("Confirm the database connection and apply the latest migrations before using this workspace.")
