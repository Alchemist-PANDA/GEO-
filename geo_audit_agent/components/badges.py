def severity_badge(severity: str) -> str:
    """Return HTML for severity/priority badges."""
    sev = severity.lower().strip()
    colors = {
        "critical": {"bg": "rgba(239, 68, 68, 0.15)", "text": "#EF4444", "border": "rgba(239, 68, 68, 0.3)"},
        "high": {"bg": "rgba(245, 158, 11, 0.15)", "text": "#F59E0B", "border": "rgba(245, 158, 11, 0.3)"},
        "medium": {"bg": "rgba(59, 130, 246, 0.15)", "text": "#3B82F6", "border": "rgba(59, 130, 246, 0.3)"},
        "low": {"bg": "rgba(16, 185, 129, 0.15)", "text": "#10B981", "border": "rgba(16, 185, 129, 0.3)"}
    }
    style = colors.get(sev, {"bg": "rgba(156, 163, 175, 0.15)", "text": "#9CA3AF", "border": "rgba(156, 163, 175, 0.3)"})
    return f'<span class="status-pill" style="background-color: {style["bg"]}; color: {style["text"]}; border: 1px solid {style["border"]}; padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">{severity}</span>'


def status_badge(status: str) -> str:
    """Return HTML for status badges."""
    stat = status.lower().strip()
    colors = {
        "completed": {"bg": "rgba(16, 185, 129, 0.15)", "text": "#10B981", "border": "rgba(16, 185, 129, 0.3)"},
        "approved": {"bg": "rgba(16, 185, 129, 0.15)", "text": "#10B981", "border": "rgba(16, 185, 129, 0.3)"},
        "pending": {"bg": "rgba(245, 158, 11, 0.15)", "text": "#F59E0B", "border": "rgba(245, 158, 11, 0.3)"},
        "blocked": {"bg": "rgba(239, 68, 68, 0.15)", "text": "#EF4444", "border": "rgba(239, 68, 68, 0.3)"},
        "rejected": {"bg": "rgba(239, 68, 68, 0.15)", "text": "#EF4444", "border": "rgba(239, 68, 68, 0.3)"}
    }
    style = colors.get(stat, {"bg": "rgba(156, 163, 175, 0.15)", "text": "#9CA3AF", "border": "rgba(156, 163, 175, 0.3)"})
    return f'<span class="status-pill" style="background-color: {style["bg"]}; color: {style["text"]}; border: 1px solid {style["border"]}; padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">{status}</span>'
