"""Reusable Copilot affordances attached to charts and metrics.

Every chart/metric on the dashboard gets a small icon-only button. Clicking
it stashes the relevant context in session_state and navigates to the
Copilot page via st.switch_page — no floating panels, no custom CSS hacks.
"""

import streamlit as st


def _go_to_copilot(chart_title: str, chart_data, fig_json: str | None):
    st.session_state.copilot_context = {
        "chart_title": chart_title,
        "chart_data": chart_data,
        "fig_json": fig_json,
    }
    st.session_state.copilot_auto_ask = f"Explain this chart: {chart_title}"
    st.switch_page("pages/3_🤖_Copilot.py")


def render_chart_with_copilot(fig, chart_title: str, chart_data=None, key: str | None = None, height: int | None = None):
    """Render a Plotly figure with a small 💬 Copilot icon button beneath it."""
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, use_container_width=True, key=f"{key}_chart" if key else None)

    btn_key = f"copilot_btn_{key or chart_title}"
    _, icon_col = st.columns([20, 1])
    with icon_col:
        if st.button("💬", key=btn_key, help=f"Ask Copilot about {chart_title}"):
            import plotly.io as pio
            _go_to_copilot(chart_title, chart_data, pio.to_json(fig))


def copilot_icon_button(topic: str, data=None, key: str | None = None):
    """Generic icon-only Copilot trigger for non-Plotly elements (HTML gauges, metrics, tables)."""
    btn_key = f"copilot_icon_{key or topic}"
    if st.button("🤖", key=btn_key, help=f"Ask Copilot about {topic}"):
        _go_to_copilot(topic, data, None)
