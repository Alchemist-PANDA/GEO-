import streamlit as st

from geo_audit_agent.components.cards import priority_card_html


def render_gap_matrix(gaps):
    """Render the gaps in a 2x2 visual priority matrix."""
    st.markdown("""
        <div style="margin-bottom: 25px;">
            <h3 style="margin-top: 0; margin-bottom: 5px; font-size: 1.25rem;">🚩 Brand Entity Priority Matrix</h3>
            <p style="color: #64748B; font-size: 0.9rem; margin-top: 0; margin-bottom: 20px;">
                Actionable roadmap prioritized by search impact severity. Implement fixes starting with Critical/High items.
            </p>
        </div>
    """, unsafe_allow_html=True)

    critical_gaps = []
    high_gaps = []
    medium_gaps = []
    low_gaps = []

    for gap in gaps:
        sev = gap.get("severity", "Medium").title()
        if sev == "Critical":
            critical_gaps.append(gap)
        elif sev == "High":
            high_gaps.append(gap)
        elif sev == "Medium":
            medium_gaps.append(gap)
        elif sev == "Low":
            low_gaps.append(gap)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            <div style="background: rgba(239, 68, 68, 0.03); border: 1px solid rgba(239, 68, 68, 0.15); border-radius: 12px; padding: 16px; margin-bottom: 16px; min-height: 250px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; border-bottom: 1px solid rgba(239, 68, 68, 0.15); padding-bottom: 8px;">
                    <span style="font-size: 1.2rem;">🔴</span>
                    <h4 style="margin:0; font-weight:700; color:#EF4444;">CRITICAL <span style="font-size: 0.8rem; font-weight:500; color:#64748B;">(Fix Now)</span></h4>
                </div>
        """, unsafe_allow_html=True)
        if critical_gaps:
            for g in critical_gaps:
                st.markdown(priority_card_html(g.get("gap_type", "Unknown Gap"), g.get("description", ""), "Critical"), unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#64748B; font-style:italic; font-size:0.85rem; margin-top: 20px;">No critical gaps detected. Good job!</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
            <div style="background: rgba(59, 130, 246, 0.03); border: 1px solid rgba(59, 130, 246, 0.15); border-radius: 12px; padding: 16px; min-height: 250px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; border-bottom: 1px solid rgba(59, 130, 246, 0.15); padding-bottom: 8px;">
                    <span style="font-size: 1.2rem;">🔵</span>
                    <h4 style="margin:0; font-weight:700; color:#3B82F6;">MEDIUM <span style="font-size: 0.8rem; font-weight:500; color:#64748B;">(Fix This Month)</span></h4>
                </div>
        """, unsafe_allow_html=True)
        if medium_gaps:
            for g in medium_gaps:
                st.markdown(priority_card_html(g.get("gap_type", "Unknown Gap"), g.get("description", ""), "Medium"), unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#64748B; font-style:italic; font-size:0.85rem; margin-top: 20px;">No medium-priority gaps detected.</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div style="background: rgba(245, 158, 11, 0.03); border: 1px solid rgba(245, 158, 11, 0.15); border-radius: 12px; padding: 16px; margin-bottom: 16px; min-height: 250px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; border-bottom: 1px solid rgba(245, 158, 11, 0.15); padding-bottom: 8px;">
                    <span style="font-size: 1.2rem;">🟡</span>
                    <h4 style="margin:0; font-weight:700; color:#F59E0B;">HIGH <span style="font-size: 0.8rem; font-weight:500; color:#64748B;">(Fix This Week)</span></h4>
                </div>
        """, unsafe_allow_html=True)
        if high_gaps:
            for g in high_gaps:
                st.markdown(priority_card_html(g.get("gap_type", "Unknown Gap"), g.get("description", ""), "High"), unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#64748B; font-style:italic; font-size:0.85rem; margin-top: 20px;">No high-priority gaps detected.</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
            <div style="background: rgba(16, 185, 129, 0.03); border: 1px solid rgba(16, 185, 129, 0.15); border-radius: 12px; padding: 16px; min-height: 250px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; border-bottom: 1px solid rgba(16, 185, 129, 0.15); padding-bottom: 8px;">
                    <span style="font-size: 1.2rem;">🟢</span>
                    <h4 style="margin:0; font-weight:700; color:#10B981;">LOW <span style="font-size: 0.8rem; font-weight:500; color:#64748B;">(Nice to Have)</span></h4>
                </div>
        """, unsafe_allow_html=True)
        if low_gaps:
            for g in low_gaps:
                st.markdown(priority_card_html(g.get("gap_type", "Unknown Gap"), g.get("description", ""), "Low"), unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#64748B; font-style:italic; font-size:0.85rem; margin-top: 20px;">No low-priority gaps detected.</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
