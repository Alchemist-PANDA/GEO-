import streamlit as st

def render_copilot_fab():
    """Render the floating Copilot button (bottom-right corner)."""
    st.markdown("""
    <style>
    .copilot-fab-button {
        position: fixed;
        bottom: 24px;
        right: 24px;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        box-shadow: 0 4px 16px rgba(124, 58, 237, 0.4);
        z-index: 999999;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
    }
    .copilot-fab-button:hover {
        transform: scale(1.1) rotate(5deg);
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.6);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # We use a standard Streamlit button in a sidebar/footer or floating column to toggle the state.
    # To keep layout clean and simple, we place it in sidebar bottom.
    st.sidebar.markdown("---")
    if st.sidebar.button("🤖 Open Copilot Panel", key="toggle_copilot_sidebar", use_container_width=True):
        st.session_state["copilot_open"] = not st.session_state.get("copilot_open", False)
        st.rerun()
