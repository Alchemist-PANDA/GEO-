"""BrandSight GEO Streamlit entry point."""

from geo_audit_agent.ui.audit_workspace import render_audit_workspace
from geo_audit_agent.ui.theme import apply_theme

render_audit_workspace()
apply_theme()
