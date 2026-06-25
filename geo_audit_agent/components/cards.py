from geo_audit_agent.components.badges import severity_badge, status_badge

def priority_card_html(title: str, description: str, severity: str) -> str:
    """Generate HTML for a priority card with color coding and glassmorphism."""
    sev = severity.title()
    colors = {
        "Critical": "#EF4444",
        "High": "#F59E0B",
        "Medium": "#3B82F6",
        "Low": "#10B981"
    }
    border_color = colors.get(sev, "#9CA3AF")
    
    badge = severity_badge(severity)
    
    return f"""
    <div class="priority-card {sev.lower()}" style="border-left: 4px solid {border_color}; margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <h4 style="margin: 0; font-size: 1rem; font-weight: 700; color: #FFFFFF;">{title}</h4>
            {badge}
        </div>
        <p style="margin: 0; font-size: 0.85rem; color: #94A3B8; line-height: 1.4;">{description}</p>
    </div>
    """


def action_card_header_html(title: str, status: str, impact: str, effort: str) -> str:
    """Generate HTML for the header of an action card in the Remediation Hub."""
    status_indicator = status_badge(status)
    
    # Effort/Impact badges
    impact_color = "#EF4444" if impact.lower() == "high" else "#3B82F6" if impact.lower() == "medium" else "#10B981"
    effort_color = "#10B981" if effort.lower() == "low" else "#F59E0B" if effort.lower() == "medium" else "#EF4444"
    
    is_quick_win = impact.lower() == "high" and effort.lower() == "low"
    quick_win_badge = '<span style="background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%); color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; margin-left: 8px;">🚀 QUICK WIN</span>' if is_quick_win else ''
    
    return f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 10px;">
        <div>
            <h3 style="margin: 0 0 6px 0; font-size: 1.15rem; font-weight: 700; color: #FFFFFF; display: flex; align-items: center;">
                🛠️ {title} {quick_win_badge}
            </h3>
            <div style="display: flex; gap: 10px; font-size: 0.75rem; color: #94A3B8;">
                <span>🎯 Impact: <strong style="color: {impact_color};">{impact.upper()}</strong></span>
                <span>•</span>
                <span>⏱️ Effort: <strong style="color: {effort_color};">{effort.upper()}</strong></span>
            </div>
        </div>
        <div>
            {status_indicator}
        </div>
    </div>
    """
