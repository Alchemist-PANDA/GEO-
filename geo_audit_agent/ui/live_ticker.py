import streamlit as st


def render_live_ticker(brand_name):
    """Render the real-time activity feed/live ticker."""
    st.markdown("""
        <div style="margin-bottom: 15px;">
            <h3 style="margin-top: 0; margin-bottom: 5px; font-size: 1.25rem;">🔄 Live Activity Feed</h3>
            <p style="color: #64748B; font-size: 0.9rem; margin-top: 0; margin-bottom: 15px;">
                Real-time tracking of search visibility updates and remediation deployment.
            </p>
        </div>
    """, unsafe_allow_html=True)

    activities = [
        {"time": "06:25 AM", "status": "✅", "text": f"JSON-LD schema generated for {brand_name}"},
        {"time": "06:24 AM", "status": "📈", "text": "Brand visibility increased 2.3% on ChatGPT"},
        {"time": "06:22 AM", "status": "📝", "text": "New gap detected: Missing mobile menu page"},
        {"time": "06:20 AM", "status": "🛠️", "text": "Remediation completed: FAQ section added to website"},
        {"time": "06:15 AM", "status": "🔔", "text": f"{brand_name} mentioned on local business listings"}
    ]

    st.markdown('<div style="background: rgba(255, 255, 255, 0.85); border: 1px solid rgba(124, 58, 237, 0.08); border-radius: 12px; padding: 16px; box-shadow: 0 4px 12px -2px rgba(0,0,0,0.04);">', unsafe_allow_html=True)

    for act in activities:
        st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 1.1rem;">{act['status']}</span>
                    <span style="font-size: 0.9rem; color: #1E293B;">{act['text']}</span>
                </div>
                <div style="font-size: 0.8rem; color: #64748B; font-weight: 500;">
                    {act['time']}
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
