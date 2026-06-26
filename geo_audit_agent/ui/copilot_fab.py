import streamlit as st

def render_copilot_fab():
    """Render the floating Copilot button (bottom-right corner)."""
    if "copilot" not in st.session_state:
        st.session_state.copilot = {"panel_open": False, "context": {}, "prefill": None, "messages": []}

    st.markdown("""
    <style>
    /* Target the container of the FAB button to make it float */
    div[data-testid="stButton"] button:has(div:contains("🤖")) {
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
        border: none;
    }
    div[data-testid="stButton"] button:has(div:contains("🤖")):hover {
        transform: scale(1.1) rotate(5deg);
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.6);
    }
    /* Hide the paragraph text inside the button to just show the emoji */
    div[data-testid="stButton"] button:has(div:contains("🤖")) p {
        font-size: 24px;
        margin: 0;
        padding: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("🤖", key="copilot_fab", use_container_width=False):
        st.switch_page("pages/3_🤖_Copilot.py")
