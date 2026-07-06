"""Builds a flat, JSON-friendly context dict from Streamlit session state.

Both the mock engine and the live (Anthropic) engine consume this same
shape, so the Copilot's knowledge of the app never drifts between modes.
"""

import streamlit as st


def build_context() -> dict:
    audit_results = st.session_state.get("audit_results") or {}
    multi_model_results = st.session_state.get("multi_model_results") or {}
    competitor_data = st.session_state.get("competitor_data") or {}

    brand_scores = competitor_data.get("brand_scores", {}) if competitor_data else {}
    summary = competitor_data.get("summary", {}) if competitor_data else {}

    return {
        "brand_name": audit_results.get("brand_name") or st.session_state.get("brand_name", "Your Brand"),
        "category": audit_results.get("category", ""),
        "city": audit_results.get("city", ""),
        "confidence_score": audit_results.get("confidence_score"),
        "is_cited": audit_results.get("is_cited"),
        "gaps": audit_results.get("gaps", []),
        "geo_coverage_score": (multi_model_results.get("summary") or {}).get("geo_coverage_score"),
        "model_results": multi_model_results.get("results", []) if multi_model_results else [],
        "competitor_summary": summary,
        "competitors": competitor_data.get("competitors", []) if competitor_data else [],
        "brand_scores": brand_scores,
        "chart_title": None,
        "chart_data": None,
        "fig_json": None,
    }
