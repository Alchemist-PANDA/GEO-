from __future__ import annotations

import os
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from geo_audit_agent.metrics.visibility_metrics import calculate_visibility_metrics
from geo_audit_agent.services.public_evidence import crawl_public_evidence
from geo_audit_agent.ui.access import auth_configured
from geo_audit_agent.ui.audit_context import (
    activate_audit_context,
    audit_csv,
    audit_json,
    audit_markdown,
    build_audit_context,
)
from geo_audit_agent.ui.theme import apply_theme, render_hero
from multi_model import run_multi_model_audit


def _metric_rows(results: list[dict]) -> list[dict]:
    return [
        {
            "provider": result.get("provider"),
            "prompt_id": result.get("prompt_id"),
            "mode": result.get("mode"),
            "mentioned": result.get("mentioned"),
            "recommended": result.get("recommended", result.get("recommendation", False)),
            "position": result.get("position"),
            "citation_urls": result.get("citation_urls", []),
            "sentiment": result.get("sentiment"),
            "error": result.get("error"),
        }
        for result in results
    ]


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
            st.warning("Demo fixture. This response did not come from the named provider.")
        citation_urls = result.get("citation_urls") or []
        if citation_urls:
            st.markdown("**Detected source URLs**")
            for url in citation_urls:
                st.write(url)
        st.caption(
            f"Mention: {result.get('mentioned', False)} · Recommendation: "
            f"{result.get('recommended', result.get('recommendation', False))} · "
            f"Sentiment: {result.get('sentiment', 'unknown')}"
        )
        st.code(result.get("raw_response") or "No response body", language=None)


def _render_product_overview() -> None:
    st.markdown(
        """
        <div class="bs-section-title">
          <h2>From fragmented answers to an evidence-backed operating view</h2>
          <p>BrandSight gives brand, SEO, and growth teams one controlled workspace for collection, interpretation, and action.</p>
        </div>
        <div class="bs-card-grid">
          <article class="bs-card">
            <div class="bs-card-icon">01</div>
            <h3>Measure consistently</h3>
            <p>Run the same market question across supported providers and retain the raw response, prompt version, mode, and latency.</p>
            <small>Comparable observations</small>
          </article>
          <article class="bs-card">
            <div class="bs-card-icon">02</div>
            <h3>Explain with evidence</h3>
            <p>Review what was actually observed before using the Copilot to interpret visibility gaps and competitive context.</p>
            <small>Traceable interpretation</small>
          </article>
          <article class="bs-card">
            <div class="bs-card-icon">03</div>
            <h3>Act with control</h3>
            <p>Turn verified gaps into an approval-based action plan rather than allowing an autonomous system to make unsupported changes.</p>
            <small>Human-governed execution</small>
          </article>
        </div>
        <div class="bs-trustbar">
          <span class="bs-trustpill">No silent fixture fallback</span>
          <span class="bs-trustpill">Raw evidence retained</span>
          <span class="bs-trustpill">Source-aware metrics</span>
          <span class="bs-trustpill">Approval-gated actions</span>
          <span class="bs-trustpill">Exportable audit record</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_start_steps() -> None:
    st.markdown(
        """
        <div class="bs-section-title">
          <h2>Start with one market question</h2>
          <p>The first useful result should take minutes, not a lengthy implementation project.</p>
        </div>
        <div class="bs-step-grid">
          <div class="bs-step"><div class="bs-step-num">1</div><h3>Define the brand</h3><p>Enter the brand, category, and target market you want to evaluate.</p></div>
          <div class="bs-step"><div class="bs-step-num">2</div><h3>Collect observations</h3><p>Use live providers when configured, or explore the disclosed fixture workflow safely.</p></div>
          <div class="bs-step"><div class="bs-step-num">3</div><h3>Review before action</h3><p>Inspect evidence, ask the Copilot, and approve only the recommendations you trust.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_workspace_navigation() -> None:
    st.markdown(
        """
        <div class="bs-section-title">
          <h2>Specialist workspaces</h2>
          <p>Each workspace has one clear responsibility. This keeps evidence, interpretation, action, and governance separate.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    modules = [
        ("Audit Studio", "Measure visibility and inspect raw provider evidence.", "pages/1_📈_Audit_Tool.py"),
        ("GEO Copilot", "Explore the selected audit through a guided conversation.", "pages/3_🤖_Copilot.py"),
        ("Action Agent", "Convert verified gaps into an approval-based execution plan.", "pages/4_⚡_Action_Agent.py"),
        ("Quality Inspector", "Review QA verdicts, guardrail events, and proposals.", "pages/5_🔍_Inspector.py"),
        ("Workflow Console", "Inspect orchestration state, controls, and execution traces.", "pages/6_🧠_Agentic_Workflow.py"),
        ("Billing & usage", "Review plan limits, usage, and billing requests.", "pages/7_⚡_Billing.py"),
    ]
    for offset in range(0, len(modules), 3):
        columns = st.columns(3)
        for index, (column, (label, description, page)) in enumerate(
            zip(columns, modules[offset : offset + 3], strict=False), start=offset + 1
        ):
            with column:
                with st.container(border=True):
                    st.caption(f"WORKSPACE {index:02d}")
                    st.markdown(f"### {label}")
                    st.write(description)
                    st.page_link(page, label=f"Open {label}", width="stretch")


def render_audit_workspace() -> None:
    st.set_page_config(
        page_title="BrandSight GEO",
        page_icon="🌐",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()

    render_hero(
        "Understand how AI systems represent your brand.",
        "Collect comparable provider observations, retain the evidence, and turn verified visibility gaps into controlled action.",
        kicker="BrandSight GEO · AI visibility operations",
    )
    _render_product_overview()
    _render_start_steps()

    authenticated_runtime = auth_configured()
    user_id = None
    if authenticated_runtime:
        from auth import require_login

        user_id = require_login().id

    with st.sidebar:
        st.markdown("## BrandSight GEO")
        st.caption("Evidence-led AI visibility operations")
        st.divider()
        provider_envs = {
            "OpenAI": "OPENAI_API_KEY",
            "Gemini": "GOOGLE_API_KEY",
            "Anthropic": "ANTHROPIC_API_KEY",
            "Perplexity": "PERPLEXITY_API_KEY",
        }
        configured = [name for name, env_name in provider_envs.items() if os.getenv(env_name)]
        with st.expander("System readiness", expanded=not authenticated_runtime):
            st.markdown(f"- Demo workspace: **Ready**\n- Authentication: **{'Ready' if authenticated_runtime else 'Not configured'}**")
            st.markdown(f"- Live providers: **{len(configured)} / {len(provider_envs)} configured**")
            if not authenticated_runtime:
                st.caption("The fixture workflow is available without credentials and is clearly labelled.")
        st.subheader("Audit configuration")
        allowed_modes = ["Demo fixture"] if not authenticated_runtime else ["Live providers", "Demo fixture"]
        execution_mode = st.radio("Execution mode", allowed_modes)
        if execution_mode == "Demo fixture":
            st.info("Fixture results are illustrative and excluded from authoritative metrics.")
        else:
            st.caption("Configured providers: " + (", ".join(configured) if configured else "none"))

        history = list(st.session_state.get("audit_history") or [])
        if history:
            st.divider()
            st.subheader("Session history")
            labels = {
                item["id"]: f"{item['brand_name']} · {item['city']} · {item.get('run_at', '')[:16]}"
                for item in history
            }
            ids = list(labels)
            active_id = st.session_state.get("active_audit_id")
            selected_id = st.selectbox(
                "Active audit",
                ids,
                index=ids.index(active_id) if active_id in ids else 0,
                format_func=labels.get,
            )
            if selected_id != active_id:
                selected = next(item for item in history if item["id"] == selected_id)
                activate_audit_context(st.session_state, selected)

    _render_workspace_navigation()
    st.markdown(
        """
        <div class="bs-section-title">
          <h2>Run a visibility audit</h2>
          <p>This audit becomes the shared evidence context for the Copilot, Action Agent, and workflow console.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not authenticated_runtime:
        st.info("You are viewing the evaluation workspace. Live execution is disabled until authentication and provider credentials are configured.")

    with st.form("evidence_audit"):
        col1, col2, col3 = st.columns(3)
        brand = col1.text_input("Brand", placeholder="Acme Coffee")
        category = col2.text_input("Category", placeholder="Coffee shop")
        city = col3.text_input("Market", placeholder="Islamabad")
        website_url = st.text_input("Website URL (optional — collect public evidence)", placeholder="https://example.com")
        submitted = st.form_submit_button("Run visibility audit", type="primary", use_container_width=True)

    if submitted:
        if not all(value.strip() for value in (brand, category, city)):
            st.error("Brand, category, and market are required.")
        else:
            use_real = execution_mode == "Live providers"
            with st.spinner("Collecting provider observations…"):
                raw_audit = run_multi_model_audit(
                    brand.strip(), category.strip(), city.strip(), use_real=use_real, user_id=user_id
                )
                if website_url.strip():
                    try:
                        raw_audit["public_evidence"] = crawl_public_evidence(website_url.strip())
                    except Exception as exc:
                        raw_audit["public_evidence"] = {
                            "url": website_url.strip(),
                            "status": "unavailable",
                            "error_type": type(exc).__name__,
                            "evidence_urls": [],
                        }
                audit_input = {
                    "brand": brand.strip(),
                    "category": category.strip(),
                    "city": city.strip(),
                    "run_at": datetime.now(timezone.utc).isoformat(),
                    "requested_mode": "live" if use_real else "fixture",
                }
                if raw_audit.get("error"):
                    st.error(raw_audit["error"])
                else:
                    context = build_audit_context(raw_audit, audit_input)
                    activate_audit_context(st.session_state, context)
                    st.success("Audit complete. The selected evidence is now available across all workspaces.")

    context = st.session_state.get("active_audit")
    if not context:
        st.markdown(
            """
            <div class="bs-callout">
              <div><strong>No audit selected</strong><br><span>Run the form above to create an evidence context. No sample score is preloaded or presented as a real measurement.</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    results = context["results"]
    source = context.get("data_source", "unavailable")
    st.markdown(
        f"<div class='bs-section-title'><h2>{context['brand_name']} · {context['category']}</h2><p>{context['city']} · Audit {context['id']} · {source.upper()}</p></div>",
        unsafe_allow_html=True,
    )

    export_columns = st.columns(3)
    safe_brand = "-".join(context["brand_name"].lower().split()) or "audit"
    export_columns[0].download_button("Download JSON", audit_json(context), f"{safe_brand}-audit.json", "application/json", width="stretch")
    export_columns[1].download_button("Download CSV", audit_csv(context), f"{safe_brand}-observations.csv", "text/csv", width="stretch")
    export_columns[2].download_button("Download report", audit_markdown(context), f"{safe_brand}-report.md", "text/markdown", width="stretch")

    if source == "simulated":
        st.warning("Demo data: these observations are illustrative fixtures, not live provider measurements.")
    elif source == "unavailable":
        st.error("No provider observations were collected. Metrics are unavailable, not zero.")

    public_evidence = context.get("public_evidence") or {}
    if public_evidence:
        st.subheader("Public website evidence")
        if public_evidence.get("status") == "unavailable":
            st.warning("The website could not be collected. Recommendations based on it remain unverified.")
        else:
            st.caption(
                f"Collected from {public_evidence.get('url', 'the supplied website')} · "
                f"{public_evidence.get('text_length', 0):,} text characters · "
                f"schema: {', '.join(public_evidence.get('schema_types') or []) or 'none detected'}"
            )
            st.json({
                "title": public_evidence.get("title"),
                "meta_description": public_evidence.get("meta_description"),
                "h1": public_evidence.get("h1"),
                "contact_signals": public_evidence.get("contact_signals"),
                "evidence_urls": public_evidence.get("evidence_urls", [])[:10],
            })

    expected_providers = [result["provider"] for result in results]
    metrics = calculate_visibility_metrics(
        _metric_rows(results), expected_providers=expected_providers, expected_prompts=["category-recommendation"]
    )
    metric_data = metrics.as_dict(include_confidence_intervals=True)
    if source == "live_api":
        cols = st.columns(3)
        for column, (title, key) in zip(
            cols,
            (("Mention rate", "mention_rate"), ("Provider coverage", "provider_coverage"), ("Prompt coverage", "prompt_coverage")),
            strict=True,
        ):
            item = metric_data[key]
            value = "Insufficient evidence" if item["value"] is None else f"{item['value']:.0%}"
            column.metric(title, value)
            column.caption(f"{item['numerator']} / {item['denominator']} · n={item['sample_size']}")
    else:
        st.info("Authoritative metrics exclude fixture and failed observations.")

    table = pd.DataFrame(
        [
            {
                "Model": row["model"],
                "Provider": row["provider"],
                "Mode": row.get("mode", "failed"),
                "Mention": row.get("mentioned"),
                "Position": row.get("position"),
                "Latency (ms)": row.get("latency_ms"),
                "Evidence": row.get("evidence"),
            }
            for row in results
        ]
    )
    st.dataframe(table, width="stretch", hide_index=True)

    st.subheader("Observation evidence")
    for result in results:
        _render_result(result)

    st.subheader("Competitors and trends")
    st.info(
        "Competitor comparison requires observations collected with the same provider, prompt, market, and time window. "
        "Trend analysis requires at least two comparable real periods."
    )
