from __future__ import annotations

import os
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from geo_audit_agent.metrics.visibility_metrics import calculate_visibility_metrics
from multi_model import run_multi_model_audit


def _auth_configured() -> bool:
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
        return True
    try:
        return "supabase" in st.secrets and bool(st.secrets["supabase"].get("url"))
    except Exception:
        return False


def _metric_rows(results: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for result in results:
        rows.append({
            "provider": result.get("provider"),
            "prompt_id": result.get("prompt_id"),
            "mode": result.get("mode"),
            "mentioned": result.get("mentioned"),
            "recommended": result.get("mentioned"),
            "position": result.get("position"),
            "citation_urls": [],
            "error": result.get("error"),
        })
    return rows


def _render_result(result: dict) -> None:
    mode = result.get("mode", "failed")
    mentioned = result.get("mentioned")
    status = "Mentioned" if mentioned is True else "Not mentioned" if mentioned is False else "Unavailable"
    with st.expander(f"{result['model']} · {status} · {mode.upper()}"):
        if mode == "failed":
            st.error(f"No observation was collected ({result.get('error', 'provider unavailable')}).")
            return
        st.caption(
            f"Provider: {result['provider']} · Prompt: {result.get('prompt_id', 'category-recommendation')} "
            f"v{result.get('prompt_version', '1.0')} · Latency: {result.get('latency_ms', 0)} ms"
        )
        if mode == "fixture":
            st.warning("Demo fixture. This text did not come from the named AI provider.")
        st.code(result.get("raw_response") or "No response body", language=None)


def render_audit_workspace() -> None:
    st.set_page_config(page_title="BrandSight GEO", page_icon="🌍", layout="wide")
    st.title("BrandSight GEO")
    st.caption("Evidence-backed AI visibility measurement")

    authenticated_runtime = _auth_configured()
    user_id = None
    if authenticated_runtime:
        from auth import require_login

        user_id = require_login().id
    if not authenticated_runtime:
        st.warning(
            "Local evaluation mode: authentication is not configured, so Live execution is disabled. "
            "Configure Supabase to enable authenticated Live audits."
        )

    with st.sidebar:
        st.header("Audit configuration")
        allowed_modes = ["Demo fixture"] if not authenticated_runtime else ["Live providers", "Demo fixture"]
        execution_mode = st.radio("Execution mode", allowed_modes)
        if execution_mode == "Demo fixture":
            st.info("Demo results are synthetic fixtures and are excluded from authoritative metrics.")
        else:
            configured = [
                name for name, env_name in {
                    "OpenAI": "OPENAI_API_KEY",
                    "Gemini": "GOOGLE_API_KEY",
                    "Anthropic": "ANTHROPIC_API_KEY",
                    "Perplexity": "PERPLEXITY_API_KEY",
                }.items() if os.getenv(env_name)
            ]
            st.caption("Configured providers: " + (", ".join(configured) if configured else "none"))

    with st.form("evidence_audit"):
        col1, col2, col3 = st.columns(3)
        brand = col1.text_input("Brand", placeholder="Acme Coffee")
        category = col2.text_input("Category", placeholder="coffee shop")
        city = col3.text_input("Market", placeholder="Islamabad")
        submitted = st.form_submit_button("Run audit", type="primary")

    if submitted:
        if not all(value.strip() for value in (brand, category, city)):
            st.error("Brand, category, and market are required.")
        else:
            use_real = execution_mode == "Live providers"
            with st.spinner("Collecting provider observations…"):
                st.session_state["verified_audit"] = run_multi_model_audit(
                    brand.strip(), category.strip(), city.strip(), use_real=use_real, user_id=user_id
                )
                st.session_state["verified_audit_input"] = {
                    "brand": brand.strip(), "category": category.strip(), "city": city.strip(),
                    "run_at": datetime.now(timezone.utc).isoformat(),
                    "requested_mode": "live" if use_real else "fixture",
                }

    audit = st.session_state.get("verified_audit")
    audit_input = st.session_state.get("verified_audit_input")
    if not audit or not audit_input:
        st.info("Run an audit to collect observations. No sample results are preloaded.")
        return

    results = audit["results"]
    source = audit["summary"].get("data_source", "unavailable")
    st.subheader(f"{audit_input['brand']} · {audit_input['category']} · {audit_input['city']}")
    st.caption(f"Run at {audit_input['run_at']} · Data source: {source.upper()}")

    if source == "simulated":
        st.error("DEMO DATA — illustrative fixtures only. These numbers are not provider measurements.")
    elif source == "unavailable":
        st.error("No provider observations were collected. Metrics are unavailable, not zero.")

    expected_providers = [result["provider"] for result in results]
    metrics = calculate_visibility_metrics(_metric_rows(results), expected_providers=expected_providers,
                                           expected_prompts=["category-recommendation"])
    metric_data = metrics.as_dict()
    if source == "live_api":
        cols = st.columns(3)
        for column, (title, key) in zip(cols, (("Mention rate", "mention_rate"),
                                               ("Provider coverage", "provider_coverage"),
                                               ("Prompt coverage", "prompt_coverage")), strict=True):
            item = metric_data[key]
            value = "Insufficient evidence" if item["value"] is None else f"{item['value']:.0%}"
            column.metric(title, value)
            column.caption(f"{item['numerator']} / {item['denominator']} · n={item['sample_size']}")
    else:
        st.info("Authoritative metrics exclude fixture and failed observations.")

    table = pd.DataFrame([{
        "Model": row["model"],
        "Provider": row["provider"],
        "Mode": row.get("mode", "failed"),
        "Mention": row.get("mentioned"),
        "Position": row.get("position"),
        "Latency (ms)": row.get("latency_ms"),
        "Evidence": row.get("evidence"),
    } for row in results])
    st.dataframe(table, use_container_width=True, hide_index=True)

    st.subheader("Observation evidence")
    for result in results:
        _render_result(result)

    st.subheader("Competitors and trends")
    st.info(
        "Not available from this sample. Competitor comparisons require observations collected with the same "
        "provider, prompt, market, and time window; trends require at least two comparable real periods."
    )
