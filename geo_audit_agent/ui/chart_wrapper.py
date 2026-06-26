import streamlit as st
import json
import plotly.graph_objects as go

def render_chart_with_explain_button(fig: go.Figure, chart_title: str, chart_data: dict, tab_name: str = "Brand Visibility", **kwargs):
    """
    Renders a Plotly figure and adds a '💡 Explain This Chart' button underneath it.
    """
    if "use_container_width" not in kwargs:
        kwargs["use_container_width"] = True
    st.plotly_chart(fig, **kwargs)
    base_key = kwargs.get("key", chart_title.replace(' ', '_'))
    button_key = f"explain_{base_key}"
    
    def on_explain():
        if "copilot" not in st.session_state:
            st.session_state.copilot = {"panel_open": False, "context": {}, "prefill": None, "messages": []}
            
        # Ensure copilot state is correctly synchronized
        st.session_state["copilot_open"] = True
        
        # Populate context and pre-fill prompt
        st.session_state.copilot["context"] = {
            "chart_title": chart_title,
            "chart_data": chart_data,
            "tab": tab_name
        }
        
        # We also set the legacy state variables that mock_engine.py relies on
        st.session_state["chart_title"] = chart_title
        st.session_state["chart_data"] = json.dumps(chart_data)
        
        # Pre-fill the question
        st.session_state.copilot["prefill"] = f"Explain this chart: {chart_title}"
        st.session_state["copilot_pending_message"] = f"Explain this chart: {chart_title}"
        st.switch_page("pages/3_Copilot.py")

    st.button("💡 Explain This Chart", key=button_key, on_click=on_explain)
