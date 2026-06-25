import streamlit as st


def render_live_ticker(brand_name):
    """Render the real-time activity feed/live ticker."""
    st.markdown("""
        <div style="margin-bottom: 15px;">
            <h3 style="margin-top: 0; margin-bottom: 5px; font-size: 1.25rem;">🔄 Live Activity Feed</h3>
            <p style="color: #94A3B8; font-size: 0.9rem; margin-top: 0; margin-bottom: 15px;">
                Real-time tracking of search visibility updates and remediation deployment.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Custom styled log list
    activities = [
        {"time": "06:25 AM", "status": "✅", "text": f"JSON-LD schema generated for {brand_name}"},
        {"time": "06:24 AM", "status": "📈", "text": "Brand visibility increased 2.3% on ChatGPT"},
        {"time": "06:22 AM", "status": "📝", "text": "New gap detected: Missing mobile menu page"},
        {"time": "06:20 AM", "status": "🛠️", "text": "Remediation completed: FAQ section added to website"},
        {"time": "06:15 AM", "status": "🔔", "text": f"{brand_name} mentioned on local business listings"}
    ]
    
    st.markdown('<div style="background: rgba(26, 26, 46, 0.45); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 16px;">', unsafe_allow_html=True)
    
    for act in activities:
        st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 1.1rem;">{act['status']}</span>
                    <span style="font-size: 0.9rem; color: #E2E8F0;">{act['text']}</span>
                </div>
                <div style="font-size: 0.8rem; color: #64748B; font-weight: 500;">
                    {act['time']}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("""
        <div style="text-align: center; margin-top: 12px;">
            <a href="#" style="font-size: 0.85rem; color: #7C3AED; font-weight: 600; text-decoration: none;">View All Activity →</a>
        </div>
        </div>
    """, unsafe_allow_html=True)
