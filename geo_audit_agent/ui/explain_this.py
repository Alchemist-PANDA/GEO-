import streamlit as st
import json

def explain_this(element_type: str, element_id: str, context_data: dict):
    """
    Render an 'Explain This' button next to a chart/metric/table.
    """
    button_key = f"explain_{element_type}_{element_id}"

    st.markdown(f"""
    <style>
    .explain-btn {{
        background: rgba(124, 58, 237, 0.08);
        border: 1px solid rgba(124, 58, 237, 0.15);
        border-radius: 8px;
        padding: 4px 12px;
        color: #7C3AED;
        font-size: 12px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }}
    .explain-btn:hover {{
        background: rgba(124, 58, 237, 0.15);
        transform: translateY(-1px);
    }}
    </style>
    """, unsafe_allow_html=True)

    if st.button(f"💡 Explain This {element_type.title()}", key=button_key):
        prompt = f"Explain this {element_type} to me in simple terms. Here's the data: {json.dumps(context_data)}"
        
        # Open side panel/sidebar copilot
        st.session_state["copilot_open"] = True
        st.session_state["copilot_pending_message"] = prompt
        
        # Add to message list directly to trigger processing
        if "copilot_messages" not in st.session_state:
            st.session_state["copilot_messages"] = []
        
        # We rerun to display it
        st.rerun()
