import json
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional

def build_chart(chart_type: str, title: str, data_source: str, metrics: Optional[List[str]], context: Dict[str, Any]) -> str:
    """
    Generate a Plotly figure from a Copilot tool call.

    Returns: plotly figure JSON string
    """
    fig = go.Figure()
    metrics = metrics or []

    if data_source == "competitor_comparison" and chart_type == "bar":
        competitors = context.get("competitors", []) or []
        names = [c.get("name") or "Unknown" for c in competitors]
        scores = [c.get("geo_score") or 0 for c in competitors]
        
        # Include own brand if present
        brand_name = context.get("brand_name")
        brand_score = context.get("geo_score")
        if brand_name and brand_score is not None:
            names.insert(0, f"{brand_name} (You)")
            scores.insert(0, brand_score)

        fig.add_trace(go.Bar(
            x=names, 
            y=scores, 
            marker_color="#7C3AED",
            text=scores,
            textposition='auto'
        ))

    elif data_source == "audit_scores" and chart_type == "radar":
        categories = ["GEO Score", "Citation Rate", "Sentiment"]
        geo_score = context.get("geo_score") or 0.0
        citation_rate = context.get("citation_rate") or 0.0
        
        sentiment_val = 50.0
        sentiment = context.get("sentiment", "").lower()
        if "positive" in sentiment:
            sentiment_val = 90.0
        elif "negative" in sentiment:
            sentiment_val = 10.0

        values = [geo_score, citation_rate * 100, sentiment_val]
        
        # Add start element at end to close the radar loop
        categories.append(categories[0])
        values.append(values[0])

        fig.add_trace(go.Scatterpolar(
            r=values, 
            theta=categories, 
            fill="toself",
            fillcolor="rgba(124, 58, 237, 0.2)",
            line=dict(color="#7C3AED")
        ))

    elif data_source == "gap_analysis" and chart_type == "heatmap":
        gaps = context.get("gaps", []) or []
        gap_categories = []
        gap_severities = []
        for gap in gaps[:10]:
            if isinstance(gap, dict):
                gap_categories.append(gap.get("dimension") or "Unknown")
                severity = gap.get("severity") or "info"
                val = 1
                if severity.lower() == "critical":
                    val = 4
                elif severity.lower() == "high":
                    val = 3
                elif severity.lower() == "medium":
                    val = 2
                gap_severities.append(val)

        if gap_categories:
            fig.add_trace(go.Bar(
                x=gap_categories,
                y=gap_severities,
                marker_color="#EF4444"
            ))
            fig.update_layout(
                yaxis=dict(
                    tickvals=[1, 2, 3, 4],
                    ticktext=["Info", "Medium", "High", "Critical"]
                )
            )

    # Apply styling theme
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Inter, sans-serif", color="#1E293B"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text=title, font=dict(size=16, color="#0F172A")),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    return fig.to_json()
