import streamlit as st
from geo_audit_agent.components.cards import action_card_header_html
from geo_audit_agent.components.progress import render_progress_bar

def render_remediation_hub(remediations):
    """Render the Remediation Hub action cards with custom styles and progress."""
    if not remediations:
        st.info("Run an audit to generate remediation strategies.")
        return
        
    total = len(remediations)
    completed = sum(1 for r in remediations if r.get("status") in ["Approved", "Completed"])
    progress_pct = (completed / total * 100) if total > 0 else 0.0
    
    # Progress Section
    st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 20px; margin-bottom: 24px;">
            <h3 style="margin: 0; font-size: 1.25rem; font-weight: 700; color: #FFFFFF; display: flex; justify-content: space-between; align-items: center;">
                <span>🛠️ Remediation Hub Progress</span>
                <span style="font-size: 1rem; color: #a5b4fc; font-weight: 600;">{completed}/{total} Completed</span>
            </h3>
    """, unsafe_allow_html=True)
    
    st.markdown(render_progress_bar(progress_pct, "linear-gradient(90deg, #7C3AED 0%, #10B981 100%)"), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Render individual action cards
    for idx, item in enumerate(remediations):
        tool_name = item.get("tool", "JSON-LD Generator")
        status = item.get("status", "Pending")
        content = item.get("content", "")
        
        # Determine Impact and Effort for design visuals
        if "JSON" in tool_name or "Schema" in tool_name:
            impact = "High"
            effort = "Low"
        elif "Menu" in tool_name or "Page" in tool_name:
            impact = "High"
            effort = "Medium"
        elif "FAQ" in tool_name:
            impact = "Medium"
            effort = "Low"
        else:
            impact = "Medium"
            effort = "Medium"
            
        with st.container(border=True):
            # Render styled header HTML
            st.markdown(action_card_header_html(tool_name, status, impact, effort), unsafe_allow_html=True)
            
            # Action Card Body
            tab_code, tab_preview = st.tabs(["💻 Implementation Snippet", "📝 Human-Readable Preview"])
            
            with tab_code:
                # Text area for editing the snippet
                edited_content = st.text_area(
                    "Edit Remediation Snippet",
                    value=content,
                    height=200,
                    key=f"edit_code_{idx}",
                    label_visibility="collapsed"
                )
                item['content'] = edited_content
                st.code(edited_content, language="json" if "JSON" in tool_name else "markdown")
                
            with tab_preview:
                st.markdown(edited_content)
                
            # Card Action Controls
            st.divider()
            b_col1, b_col2, b_col3, b_col4 = st.columns([1, 1, 1.2, 1.8])
            
            with b_col1:
                if st.button("✅ Approve", key=f"app_btn_{idx}", use_container_width=True):
                    item['status'] = "Approved"
                    st.toast(f"Approved {tool_name}")
                    st.rerun()
            with b_col2:
                if st.button("❌ Reject", key=f"rej_btn_{idx}", use_container_width=True):
                    item['status'] = "Rejected"
                    st.toast(f"Rejected {tool_name}")
                    st.rerun()
            with b_col3:
                st.download_button(
                    "📥 Download Snippet",
                    data=edited_content,
                    file_name=f"brandsight_{tool_name.lower().replace(' ', '_')}.txt",
                    key=f"dl_btn_{idx}",
                    use_container_width=True
                )
            with b_col4:
                if st.button("✨ Auto-Optimize Content", key=f"opt_{idx}", help="AI refinement of this content.", use_container_width=True):
                    st.warning("Auto-optimization is a premium feature.")
