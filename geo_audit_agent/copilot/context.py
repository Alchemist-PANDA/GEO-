import json
from typing import Dict, Any

def build_copilot_context(session_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assemble context from Streamlit session state for the Copilot.
    """
    context = {
        "current_tab": session_state.get("active_tab", "unknown"),
        "brand_name": session_state.get("brand_name", ""),
        "category": session_state.get("category", ""),
        "city": session_state.get("city", ""),
        "chart_title": session_state.get("chart_title", ""),
        "chart_data": session_state.get("chart_data", ""),
    }

    # Audit data (if an audit has been run)
    audit = session_state.get("audit_result")
    if audit:
        # Check if audit is a dict or string
        if isinstance(audit, str):
            try:
                audit = json.loads(audit)
            except Exception:
                audit = {}
        if isinstance(audit, dict):
            report = audit.get("report", {}) or {}
            context["geo_score"] = report.get("geo_score")
            context["citation_rate"] = report.get("citation_rate")
            context["gaps"] = audit.get("gaps", [])
            context["remediations"] = audit.get("remediations", {})
            context["sentiment"] = audit.get("sentiment")

    # Competitor data (if a scan has been run)
    competitor = session_state.get("competitor_data")
    if competitor:
        if isinstance(competitor, str):
            try:
                competitor = json.loads(competitor)
            except Exception:
                competitor = {}
        if isinstance(competitor, dict):
            context["brand_scores"] = competitor.get("brand_scores")
            competitors_list = competitor.get("competitors", []) or []
            context["competitors"] = [
                {"name": c.get("scores", {}).get("competitor"), "geo_score": c.get("scores", {}).get("geo_score")}
                for c in competitors_list if isinstance(c, dict)
            ]
            context["brand_rank"] = competitor.get("summary", {}).get("brand_rank")

    return context
