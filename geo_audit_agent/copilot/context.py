"""Builds a flat, JSON-friendly context dict from Streamlit session state.

Both the mock engine and the live (Anthropic) engine consume this same
shape, so the Copilot's knowledge of the app never drifts between modes.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import streamlit as st


def build_copilot_context(state: Mapping[str, Any]) -> dict:
    """Builds a flat, JSON-friendly context dict from a session state dictionary."""
    audit_result = state.get("audit_result") or state.get("audit_results") or {}
    audit_input = state.get("verified_audit_input") or {}
    multi_model_results = state.get("verified_audit") or state.get("multi_model_results") or {}
    competitor_data = state.get("competitor_data") or {}

    # Extract nested fields safely
    report = audit_result.get("report") or {}
    geo_score = report.get("geo_score") or audit_result.get("confidence_score")
    if geo_score is not None:
        # Convert to percentage if it's a fraction
        if isinstance(geo_score, float) and geo_score <= 1.0:
            geo_score = int(geo_score * 100)
        else:
            geo_score = int(geo_score)

    sentiment = audit_result.get("sentiment") or audit_result.get("llm_response")

    brand_scores = competitor_data.get("brand_scores", {}) if competitor_data else {}
    summary = competitor_data.get("summary", {}) if competitor_data else {}

    return {
        "current_tab": state.get("active_tab", "GEO Score"),
        "brand_name": state.get("brand_name") or audit_input.get("brand") or audit_result.get("brand_name") or "Your Brand",
        "category": state.get("category") or audit_input.get("category") or audit_result.get("category", ""),
        "city": state.get("city") or audit_input.get("city") or audit_result.get("city", ""),
        "geo_score": geo_score,
        "confidence_score": geo_score,
        "data_source": audit_result.get("data_source") or (multi_model_results.get("summary") or {}).get("data_source"),
        "sentiment": sentiment,
        "is_cited": audit_result.get("is_cited"),
        "gaps": audit_result.get("gaps", []),
        "geo_coverage_score": (multi_model_results.get("summary") or {}).get("geo_coverage_score"),
        "model_results": [
            result for result in multi_model_results.get("results", [])
            if result.get("mode") in {"live", "cached", "live_api"}
        ] if multi_model_results else [],
        "fixture_model_results": [
            result for result in multi_model_results.get("results", [])
            if result.get("mode") in {"fixture", "simulated"}
        ] if multi_model_results else [],
        "competitor_summary": summary,
        "competitors": competitor_data.get("competitors", []) if competitor_data else [],
        "brand_scores": brand_scores,
        "chart_title": None,
        "chart_data": None,
        "fig_json": None,
    }


def build_context() -> dict:
    return build_copilot_context(st.session_state)  # type: ignore[arg-type]
