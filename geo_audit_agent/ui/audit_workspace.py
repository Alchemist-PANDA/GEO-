from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from geo_audit_agent.ui.theme import apply_theme, render_empty, render_page_header

PROVIDERS = ["All", "Gemini", "OpenAI", "Claude", "Perplexity"]
STATUS_HELP = {
    "Live": "Real provider call. Included in authoritative metrics.",
    "Cached": "Previous real provider result. Included only when the selected period allows cached evidence.",
    "Demo": "Fixture or test data. Excluded from authoritative metrics.",
    "Failed": "Provider request failed. Excluded from rate calculations.",
    "Insufficient Evidence": "Not enough real observations to calculate this metric.",
    "Passed": "Validation succeeded.",
    "Quota Limited": "Quota or rate limit reached.",
    "Auth Error": "Check API key or project access.",
}


@dataclass(frozen=True)
class Metric:
    title: str
    numerator: int
    denominator: int
    status: str
    trend: str | None
    help_text: str

    @property
    def value(self) -> str:
        if self.denominator == 0:
            return "Insufficient evidence"
        return f"{self.numerator / self.denominator:.0%}"


def _seed_data() -> dict[str, Any]:
    return {
        "workspace": "BrandSight GEO Agency Workspace",
        "selected_brand": "Dental Art",
        "brands": [
            {
                "id": "dental-art",
                "name": "Dental Art",
                "website": "https://dentalart.net.pk/",
                "category": "Dental clinic",
                "city": "Lahore",
                "country": "Pakistan",
                "market": "Lahore, Pakistan",
                "target_customer": "Families and dental implant patients",
                "services": "Dental care, implants, braces, smile makeover, preventive care",
                "last_audit": "2026-07-20 19:26 UTC",
                "evidence_status": "Live",
            },
            {
                "id": "js-engineers",
                "name": "JS Engineers",
                "website": "https://jsengineers.pk/",
                "category": "HVAC and engineering services",
                "city": "Karachi, Lahore, Islamabad",
                "country": "Pakistan",
                "market": "Pakistan-wide",
                "target_customer": "Commercial and industrial buyers",
                "services": "HVAC, plumbing, firefighting, automation",
                "last_audit": "2026-07-20 19:26 UTC",
                "evidence_status": "Live",
            },
            {
                "id": "weproms",
                "name": "WeProms Digital",
                "website": "https://weproms.com/",
                "category": "SME digital marketing agency",
                "city": "Lahore",
                "country": "Pakistan",
                "market": "Pakistan, UK, UAE",
                "target_customer": "SME owners and agency clients",
                "services": "SEO, ads, CRM workflows, server-side tracking, AI-ready content",
                "last_audit": "2026-07-20 19:26 UTC",
                "evidence_status": "Live",
            },
        ],
        "metrics": [
            Metric("Mention Rate", 31, 40, "Live", "+6.0%", "How often the selected brand was mentioned in real provider observations."),
            Metric("Recommendation Rate", 23, 40, "Live", "+4.5%", "How often AI responses recommended the brand, not merely mentioned it."),
            Metric("Citation Rate", 18, 40, "Cached", "+2.0%", "How often responses included source or citation evidence."),
            Metric("Provider Coverage", 4, 4, "Live", None, "Providers with enough valid observations in the selected period."),
            Metric("Prompt Coverage", 10, 12, "Live", "+1 prompt", "Prompt corpus coverage with valid real observations."),
            Metric("Evidence Confidence", 0, 0, "Insufficient Evidence", None, "Composite confidence is withheld until enough public evidence is collected."),
        ],
        "recent_audits": [
            ["Dental Art", "Gemini", "Pakistan SME corpus", "Yes", "Yes", 2, "Live", "2026-07-20 19:26 UTC"],
            ["JS Engineers", "Gemini", "Pakistan SME corpus", "Yes", "Yes", 1, "Live", "2026-07-20 19:26 UTC"],
            ["Conatural", "Gemini", "Pakistan SME corpus", "Yes", "Yes", 3, "Live", "2026-07-20 19:26 UTC"],
            ["CORE Karachi", "Gemini", "Pakistan SME corpus", "Yes", "No", 1, "Live", "2026-07-20 19:26 UTC"],
            ["Fixture Clinic", "Demo", "Sample prompts", "Yes", "Yes", 0, "Demo", "Excluded from metrics"],
            ["Legacy Run", "Claude", "Agency prompts", "Unavailable", "Unavailable", 0, "Failed", "2026-07-18 10:00 UTC"],
        ],
        "observations": [
            ["Gemini", "Best dental clinic in Lahore for implants", "Dental Art", 2, "Yes", 2, "Live", "b9ea7fa1505f", "2026-07-20 19:26 UTC"],
            ["Gemini", "Which HVAC company should a commercial building in Karachi consider?", "JS Engineers", 1, "Yes", 1, "Live", "95645d580d57", "2026-07-20 19:26 UTC"],
            ["Gemini", "Best bookkeeping service for small businesses in Pakistan", "Virtual Accountants", 3, "Yes", 0, "Live", "2f7a287ab233", "2026-07-20 19:26 UTC"],
            ["Claude", "Best fitness studio in Karachi", "CORE Karachi", None, "No", 0, "Cached", "a9e7df8eb2df", "2026-07-19 09:15 UTC"],
            ["Demo", "Sample ecommerce skincare prompt", "Conatural", 1, "Yes", 0, "Demo", "fixture-only", "Excluded"],
        ],
        "validation_runs": [
            ["gemini-pk-sme-20260720", "Gemini", "gemini-3.1-flash-lite", 8, 8, 8, 0, 5, "On", "No", "2026-07-20 19:26 UTC", "validation_artifacts/gemini/pakistan_sme_case_study.json"],
            ["gemini-smoke-20260720", "Gemini", "gemini-3.1-flash-lite", 2, 2, 2, 0, 5, "On", "No", "2026-07-20 19:21 UTC", "ignored smoke artifact"],
            ["fixture-demo", "Demo", "fixture", 4, 4, 4, 0, 0, "Off", "Yes", "session", "not authoritative"],
        ],
    }


def _badge(status: str) -> str:
    key = status.lower().replace(" ", "-")
    return f"<span class='bs-badge bs-badge-{key}' title='{escape(STATUS_HELP.get(status, status))}'>{escape(status)}</span>"


def _metric_card(metric: Metric) -> None:
    trend = metric.trend or "No comparable trend"
    st.markdown(
        f"""
        <article class="bs-metric-card">
          <div class="bs-metric-top">
            <span>{escape(metric.title)}</span>
            {_badge(metric.status)}
          </div>
          <strong>{escape(metric.value)}</strong>
          <div class="bs-metric-denom">{metric.numerator} / {metric.denominator} observations</div>
          <div class="bs-metric-foot">
            <span>{escape(trend)}</span>
            <span title="{escape(metric.help_text)}">Info</span>
          </div>
        </article>
        """,
        unsafe_allow_html=True,
    )


def _section_card(title: str, body: str, status: str | None = None) -> None:
    status_html = _badge(status) if status else ""
    st.markdown(
        f"""
        <section class="bs-panel">
          <div class="bs-panel-head"><h3>{escape(title)}</h3>{status_html}</div>
          <p>{escape(body)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _top_bar(data: dict[str, Any]) -> tuple[str, str, str]:
    with st.container():
        st.markdown("<div class='bs-topbar'>", unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns([2.3, 2.1, 1.6, 1.6, 1.2])
        col1.markdown(f"**{data['workspace']}**")
        selected_brand = col2.selectbox(
            "Current selected brand",
            [brand["name"] for brand in data["brands"]],
            key="topbar_selected_brand",
            label_visibility="collapsed",
        )
        date_range = col3.selectbox(
            "Date range",
            ["Last 30 days", "Last 7 days", "This quarter", "Custom"],
            key="topbar_date_range",
            label_visibility="collapsed",
        )
        provider = col4.selectbox("Provider", PROVIDERS, key="dashboard_provider_filter", label_visibility="collapsed")
        col5.button("Run Audit", key="topbar_run_audit_button", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    return selected_brand, date_range, provider


def _sidebar() -> str:
    st.sidebar.markdown("## BrandSight GEO")
    st.sidebar.caption("Observed AI visibility for SMEs")
    st.sidebar.divider()
    nav = [
        "Dashboard",
        "New Audit",
        "Brands",
        "Competitors",
        "AI Visibility",
        "Public Evidence",
        "Reports",
        "Validation Runs",
        "Settings",
    ]
    return st.sidebar.radio("Navigation", nav, label_visibility="collapsed")


def _visibility_charts() -> None:
    trend_df = pd.DataFrame(
        {
            "Date": pd.date_range("2026-07-01", periods=6, freq="4D"),
            "Mention Rate": [0.46, 0.49, 0.52, 0.60, 0.68, 0.78],
            "Recommendation Rate": [0.31, 0.34, 0.37, 0.42, 0.50, 0.58],
        }
    )
    provider_df = pd.DataFrame(
        {
            "Provider": ["Gemini", "OpenAI", "Claude", "Perplexity"],
            "Mention Rate": [0.78, 0.64, 0.55, 0.48],
            "Recommendation Rate": [0.58, 0.50, 0.42, 0.36],
        }
    )
    prompt_df = pd.DataFrame(
        {"Prompt Category": ["Local intent", "Comparison", "Buyer-ready", "Problem-based"], "Mention Rate": [0.82, 0.64, 0.58, 0.50]}
    )
    competitor_df = pd.DataFrame(
        {"Entity": ["Selected brand", "Competitor A", "Competitor B", "Competitor C"], "Mention Share": [0.39, 0.28, 0.21, 0.12]}
    )
    confidence_df = pd.DataFrame({"Confidence": ["High", "Medium", "Low", "Insufficient"], "Observations": [12, 18, 7, 3]})

    col1, col2 = st.columns(2)
    col1.plotly_chart(px.line(trend_df, x="Date", y=["Mention Rate", "Recommendation Rate"], markers=True, title="AI visibility trend over time"), use_container_width=True)
    col2.plotly_chart(px.bar(provider_df, x="Provider", y=["Mention Rate", "Recommendation Rate"], barmode="group", title="Provider comparison"), use_container_width=True)
    col3, col4, col5 = st.columns(3)
    col3.plotly_chart(px.bar(prompt_df, x="Prompt Category", y="Mention Rate", title="Prompt category performance"), use_container_width=True)
    col4.plotly_chart(px.bar(competitor_df, x="Entity", y="Mention Share", title="Competitor visibility comparison"), use_container_width=True)
    col5.plotly_chart(px.pie(confidence_df, names="Confidence", values="Observations", title="Evidence confidence distribution", hole=0.45), use_container_width=True)


def _dashboard(data: dict[str, Any], provider: str) -> None:
    render_page_header("Dashboard", "AI Visibility Dashboard", "Track how often your brand appears, is recommended, and is supported by evidence in AI answers.")
    metric_cols = st.columns(3)
    for index, metric in enumerate(data["metrics"]):
        with metric_cols[index % 3]:
            _metric_card(metric)
    st.divider()
    _visibility_charts()
    st.subheader("Recent audits")
    rows = data["recent_audits"]
    if provider != "All":
        rows = [row for row in rows if row[1] == provider]
    if not rows:
        render_empty("No data", "No real AI visibility observations yet.", "Run your first audit.")
    else:
        df = pd.DataFrame(rows, columns=["Brand", "Provider", "Prompt set", "Mentioned?", "Recommended?", "Citations", "Status", "Run date"])
        st.dataframe(df, use_container_width=True, hide_index=True)


def _new_audit() -> None:
    render_page_header("Audit", "New GEO Audit", "Configure a real provider audit or a clearly labelled demo run for testing.")
    left, right = st.columns([2, 1], gap="large")
    with left:
        with st.form("new_audit_form"):
            st.markdown("### Business Information")
            c1, c2 = st.columns(2)
            business = c1.text_input("Business name", placeholder="Dental Art", key="new_audit_business_name")
            website = c2.text_input("Website URL", placeholder="https://example.com", key="new_audit_website_url")
            c3, c4, c5 = st.columns(3)
            category = c3.text_input("Category", placeholder="Dental clinic", key="new_audit_category")
            market = c4.text_input("City / market", placeholder="Lahore", key="new_audit_market")
            country = c5.text_input("Country", value="Pakistan", key="new_audit_country")
            business_type = st.selectbox(
                "Business type",
                ["Local service", "Ecommerce", "B2B service", "Professional service", "Restaurant", "Fitness", "Healthcare", "Legal", "Accounting", "Agency", "Other"],
                key="new_audit_business_type",
            )
            target_customer = st.text_input("Target customer", placeholder="SME owners, families, commercial buyers", key="new_audit_target_customer")
            services = st.text_area("Main services/products", placeholder="Implants, braces, preventive dental care", key="new_audit_services")
            notes = st.text_area("Optional notes", key="new_audit_notes")

            st.markdown("### Competitors")
            competitor_count = st.number_input("Competitor rows", min_value=1, max_value=6, value=2, key="new_audit_competitor_rows")
            for index in range(int(competitor_count)):
                c1, c2, c3 = st.columns(3)
                c1.text_input("Competitor name", key=f"competitor_name_{index}")
                c2.text_input("Competitor website", key=f"competitor_site_{index}")
                c3.text_input("Competitor city/market", key=f"competitor_market_{index}")

            st.markdown("### AI Providers")
            p1, p2, p3, p4 = st.columns(4)
            gemini = p1.checkbox("Gemini", value=True, key="new_audit_provider_gemini")
            openai = p2.checkbox("OpenAI", key="new_audit_provider_openai")
            claude = p3.checkbox("Claude", key="new_audit_provider_claude")
            perplexity = p4.checkbox("Perplexity", key="new_audit_provider_perplexity")
            demo_mode = st.toggle("Fixture/demo mode for testing only", key="new_audit_demo_mode")
            if demo_mode:
                st.warning("Demo mode is not real AI visibility evidence and will be excluded from authoritative metrics.")

            st.markdown("### Prompt Strategy")
            tabs = st.tabs(["Auto-generate prompts", "Manual prompts", "Import prompt corpus"])
            with tabs[0]:
                categories = st.multiselect(
                    "Auto prompt categories",
                    ["Best business in city/category", "Service recommendation", "Comparison prompt", "Problem-based prompt", "Local intent prompt", "Buyer-ready prompt"],
                    default=["Best business in city/category", "Service recommendation", "Buyer-ready prompt"],
                    key="new_audit_auto_prompt_categories",
                )
                st.caption("Examples: Best dental clinic in Lahore for implants; Which HVAC company should a commercial building in Karachi consider?")
            with tabs[1]:
                st.text_area("Manual prompts", placeholder="One prompt per line", key="new_audit_manual_prompts")
            with tabs[2]:
                st.file_uploader("Import prompt corpus", type=["json", "csv", "txt"], key="new_audit_prompt_corpus")

            st.markdown("### Quota Controls")
            q1, q2, q3, q4 = st.columns(4)
            max_requests = q1.number_input("Max requests", min_value=1, max_value=200, value=12, key="new_audit_max_requests")
            max_tokens = q2.number_input("Max output tokens", min_value=64, max_value=2048, value=384, key="new_audit_max_output_tokens")
            q3.toggle("Use key failover", value=True, key="new_audit_use_key_failover")
            q4.toggle("Stop on auth error", value=True, key="new_audit_stop_on_auth_error")
            st.slider("Provider timeout", min_value=10, max_value=120, value=45, key="new_audit_provider_timeout")

            submitted = st.form_submit_button("Run Audit", key="new_audit_run_submit", type="primary", use_container_width=True)

    selected_providers = [name for name, enabled in [("Gemini", gemini), ("OpenAI", openai), ("Claude", claude), ("Perplexity", perplexity)] if enabled]
    prompt_count = len(categories) if "categories" in locals() else 0
    with right:
        st.markdown("### Run Panel")
        _section_card("Estimated requests", f"{max_requests if 'max_requests' in locals() else 0} max requests across {len(selected_providers)} provider(s).", "Demo" if "demo_mode" in locals() and demo_mode else "Live")
        st.write(f"**Providers selected:** {', '.join(selected_providers) or 'None'}")
        st.write(f"**Brands/competitors included:** {1 + int(competitor_count) if 'competitor_count' in locals() else 1}")
        st.write(f"**Prompt count:** {prompt_count}")
        st.caption("Expected cost depends on provider pricing and output length. Use low max tokens for validation.")
        if submitted:
            if not business or not website or not category or not market:
                st.error("Business name, website, category, and market are required.")
            else:
                st.success("Audit configuration accepted.")
                for step in ["Preparing prompts", "Collecting public evidence", "Querying AI providers", "Detecting brand mentions", "Calculating metrics", "Generating report"]:
                    st.progress(100, text=step)


def _brand_detail(data: dict[str, Any], selected_brand: str) -> None:
    brand = next((item for item in data["brands"] if item["name"] == selected_brand), data["brands"][0])
    render_page_header("Brand", brand["name"], f"{brand['category']} · {brand['market']} · {brand['website']}")
    c1, c2, c3 = st.columns(3)
    c1.write(f"**Last audit:** {brand['last_audit']}")
    c2.write(f"**Evidence status:** {brand['evidence_status']}")
    c3.write(f"**Target customer:** {brand['target_customer']}")
    tabs = st.tabs(["Overview", "AI Mentions", "Recommendations", "Public Evidence", "Competitors", "Reports", "History"])
    with tabs[0]:
        cols = st.columns(3)
        for index, metric in enumerate(data["metrics"][:6]):
            with cols[index % 3]:
                _metric_card(metric)
        _section_card("Main findings summary", "Gemini can classify the brand when public service, market, and trust signals are explicit. Evidence confidence remains gated when corroboration is incomplete.", "Live")
        st.markdown("### Top 5 improvement actions")
        st.checkbox("Add or strengthen organization and local business schema", value=True, key="brand_action_schema")
        st.checkbox("Make location and service pages crawlable", value=True, key="brand_action_location_pages")
        st.checkbox("Add review proof and third-party corroboration", value=True, key="brand_action_review_proof")
        st.checkbox("Publish credentials, team, or case-study evidence where relevant", value=False, key="brand_action_credentials")
        st.checkbox("Re-test comparable prompts after implementation", value=False, key="brand_action_retest")
    with tabs[1]:
        df = pd.DataFrame(data["observations"], columns=["Provider", "Prompt", "Mentioned brand", "Mention position", "Recommended?", "Citation count", "Status", "Response hash", "Run date"])
        st.dataframe(df, use_container_width=True, hide_index=True)
        with st.expander("Response detail drawer"):
            st.write("Provider: Gemini")
            st.write("Status explanation: Live real provider observation.")
            st.write("Mention detection result: Mentioned")
            st.write("Recommendation detection result: Recommended")
            st.code("Redacted response preview unavailable in this UI mock. Use stored response hashes for audit traceability.", language=None)
    with tabs[2]:
        _section_card("Recommendation signal", "Recommendation rate is calculated only from real or allowed cached observations. Demo rows remain excluded.", "Live")
    with tabs[3]:
        _public_evidence()
    with tabs[4]:
        _competitors()
    with tabs[5]:
        _reports(data)
    with tabs[6]:
        st.line_chart(pd.DataFrame({"Mention rate": [0.46, 0.52, 0.78], "Recommendation rate": [0.31, 0.42, 0.58]}))


def _competitors() -> None:
    render_page_header("Competitors", "Competitor Comparison", "Compare visibility only when evidence is like-for-like.")
    f1, f2, f3, f4, f5 = st.columns(5)
    f1.selectbox("Brand", ["Dental Art", "JS Engineers", "WeProms Digital"], key="competitor_brand_filter")
    f2.selectbox("Competitor set", ["Local Lahore clinics", "Pakistan B2B services"], key="competitor_set_filter")
    f3.selectbox("Provider", PROVIDERS, key="competitor_provider_filter")
    f4.selectbox("Prompt category", ["All", "Local intent", "Comparison", "Buyer-ready"], key="competitor_prompt_category_filter")
    f5.selectbox("Date range", ["Last 30 days", "Last 7 days"], key="competitor_date_range_filter")
    st.warning("Like-for-like comparison unavailable when competitors do not have equal evidence.")
    df = pd.DataFrame(
        [
            ["Selected brand", "https://example.com", "78%", "58%", "45%", "10 / 12", "4 / 4", "Live"],
            ["Competitor A", "https://competitor-a.pk", "Insufficient evidence", "Insufficient evidence", "Insufficient evidence", "0 / 0", "0 / 4", "Insufficient Evidence"],
            ["Competitor B", "https://competitor-b.pk", "52%", "35%", "18%", "8 / 12", "3 / 4", "Cached"],
        ],
        columns=["Entity", "Website", "Mention rate", "Recommendation rate", "Citation rate", "Prompt coverage", "Provider coverage", "Evidence status"],
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    col1, col2 = st.columns(2)
    coverage_plot = pd.DataFrame({"Entity": ["Selected brand", "Competitor B"], "Prompt coverage": [0.83, 0.67]})
    col1.plotly_chart(px.bar(coverage_plot, x="Entity", y="Prompt coverage", title="Rank/order chart requires equal evidence"), use_container_width=True)
    share = pd.DataFrame({"Entity": ["Selected brand", "Competitor B"], "Mention share": [0.62, 0.38], "Recommendation share": [0.67, 0.33]})
    col2.plotly_chart(px.bar(share, x="Entity", y=["Mention share", "Recommendation share"], barmode="group"), use_container_width=True)


def _public_evidence() -> None:
    render_page_header("Evidence", "Public Evidence", "Show crawlable evidence that AI systems may use.")
    a, b = st.columns(2)
    with a:
        st.markdown("### Website Evidence")
        evidence = {
            "Title tag": "Present",
            "Meta description": "Present",
            "H1": "Present",
            "Canonical URL": "Present",
            "Schema types found": "Organization, LocalBusiness",
            "Social links": "Detected",
            "Contact signals": "Detected",
            "Location signals": "Needs strengthening",
            "Service/product signals": "Detected",
        }
        st.dataframe(pd.DataFrame(evidence.items(), columns=["Signal", "Status"]), use_container_width=True, hide_index=True)
    with b:
        st.markdown("### Evidence URLs")
        st.write("- Homepage")
        st.write("- Service pages")
        st.write("- Contact page")
        st.write("- About page")
        st.write("- Product/category pages")
    st.markdown("### Evidence Gaps")
    gaps = ["Missing schema", "Weak service pages", "No location page", "No review proof", "No professional credentials", "No case studies", "No third-party corroboration", "Unclear category positioning"]
    st.dataframe(pd.DataFrame({"Gap": gaps, "Priority": ["High", "High", "Medium", "High", "Medium", "Medium", "High", "Medium"]}), use_container_width=True, hide_index=True)
    st.markdown("### 30-Day Improvement Plan")
    for index, action in enumerate(
        [
            "Fix entity clarity",
            "Improve local proof",
            "Add schema",
            "Strengthen service pages",
            "Add review/citation proof",
            "Add credentials/case studies",
            "Re-test AI visibility",
        ]
    ):
        st.checkbox(action, value=action in {"Fix entity clarity", "Improve local proof"}, key=f"evidence_plan_{index}")


def _reports(data: dict[str, Any]) -> None:
    render_page_header("Reports", "Reports", "Generate client-ready reports for SME owners and agencies.")
    df = pd.DataFrame(
        [
            ["Pakistan SME Gemini Case Study", "Multiple", "2026-07-20", "Gemini", "Live", "Codex", "Export PDF", "View"],
            ["Dental Art GEO Snapshot", "Dental Art", "2026-07-20", "Gemini", "Live", "Agency user", "Export PDF", "View"],
        ],
        columns=["Report name", "Brand", "Date", "Provider coverage", "Evidence status", "Created by", "Export PDF", "View"],
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("### Report Preview")
    _section_card("Executive Summary", "Observed AI visibility is based on provider responses and public-facing evidence. Demo observations are excluded from authoritative metrics.", "Live")
    st.write("**Disclaimer:** This report is based on observed AI-provider responses and public-facing evidence. It is not a guarantee of ranking, revenue, traffic, or permanent visibility.")
    c1, c2, c3, c4 = st.columns(4)
    c1.button("Export PDF", key="report_export_pdf", use_container_width=True)
    c2.button("Export Markdown", key="report_export_markdown", use_container_width=True)
    c3.button("Export JSON", key="report_export_json", use_container_width=True)
    c4.button("Copy client summary", key="report_copy_client_summary", use_container_width=True)


def _validation_runs(data: dict[str, Any]) -> None:
    render_page_header("Validation", "Validation Runs", "Technical evidence for provider validation without exposing keys.")
    df = pd.DataFrame(
        data["validation_runs"],
        columns=["Run ID", "Provider", "Model", "Request budget", "Requests attempted", "Passed", "Failed", "Keys configured", "Failover enabled", "Fixture mode", "Generated at", "Artifact path"],
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    with st.expander("Validation detail"):
        st.write("Key slots used: GOOGLE_API_KEY through GOOGLE_API_KEY_5. Actual keys are never shown.")
        st.write("Error categories: auth_or_permission, quota_or_rate_limit, missing_key, network, provider_unavailable.")
        st.write("Interpretation: Integration evidence only; not statistically stable visibility scoring.")


def _settings() -> None:
    render_page_header("Settings", "Settings", "Configure workspace, providers, prompts, reporting, team, and retention.")
    tabs = st.tabs(["Workspace settings", "Provider settings", "API key status", "Prompt templates", "Report branding", "Team members", "Data retention"])
    with tabs[2]:
        rows = []
        for provider in ["Gemini", "OpenAI", "Claude", "Perplexity"]:
            rows.append([provider, "Configured" if provider == "Gemini" else "Missing", "2026-07-20", "" if provider == "Gemini" else "missing_key", "Test key"])
        for index in range(8):
            slot = "GOOGLE_API_KEY" if index == 0 else f"GOOGLE_API_KEY_{index}"
            status = "Configured" if index < 6 else "Failed" if index == 6 else "Missing"
            error = "" if index < 6 else "auth_or_permission" if index == 6 else "missing_key"
            action = "" if index < 6 else "Check API key or project access" if index == 6 else "Set provider API key"
            rows.append([slot, status, "2026-07-20" if index < 7 else "", error, action])
        st.dataframe(pd.DataFrame(rows, columns=["Provider / slot", "Status", "Last validated", "Last error category", "Recommended action"]), use_container_width=True, hide_index=True)
        st.caption("Actual API keys are never displayed.")
    with tabs[0]:
        st.text_input("Workspace name", value="BrandSight GEO Agency Workspace", key="settings_workspace_name")
    with tabs[1]:
        st.multiselect("Enabled providers", ["Gemini", "OpenAI", "Claude", "Perplexity"], default=["Gemini"], key="settings_enabled_providers")
    with tabs[3]:
        st.text_area("Default prompt template", value="Best {category} in {city} for {target_customer}", key="settings_default_prompt_template")
    with tabs[4]:
        st.text_input("Report footer", value="Observed AI visibility. No ranking guarantee.", key="settings_report_footer")
    with tabs[5]:
        st.dataframe(pd.DataFrame([["Owner", "Admin"], ["Analyst", "Can run audits"]], columns=["Member", "Role"]), hide_index=True)
    with tabs[6]:
        st.selectbox("Retain raw responses", ["Never commit raw responses", "30 days local only", "90 days encrypted storage"], key="settings_retention_raw_responses")


def _ai_visibility(data: dict[str, Any]) -> None:
    render_page_header("Visibility", "AI Visibility", "Review mention and recommendation observations by provider.")
    df = pd.DataFrame(data["observations"], columns=["Provider", "Prompt", "Mentioned brand", "Mention position", "Recommended?", "Citation count", "Status", "Response hash", "Run date"])
    st.dataframe(df, use_container_width=True, hide_index=True)


def _brands(data: dict[str, Any], selected_brand: str) -> None:
    render_page_header("Brands", "Brands", "Manage brands and open their GEO profiles.")
    st.dataframe(pd.DataFrame(data["brands"]), use_container_width=True, hide_index=True)
    brand_names = [brand["name"] for brand in data["brands"]]
    active_name = st.selectbox(
        "Open brand profile",
        brand_names,
        index=brand_names.index(selected_brand) if selected_brand in brand_names else 0,
        key="brand_detail_selected_brand",
    )
    brand = next(item for item in data["brands"] if item["name"] == active_name)
    st.markdown("### Brand Detail")
    cols = st.columns(4)
    cols[0].write(f"**Website:** {brand['website']}")
    cols[1].write(f"**Category:** {brand['category']}")
    cols[2].write(f"**Market:** {brand['market']}")
    cols[3].write(f"**Last audit:** {brand['last_audit']}")
    tabs = st.tabs(["Overview", "AI Mentions", "Recommendations", "Public Evidence", "Competitors", "Reports", "History"])
    with tabs[0]:
        _section_card("Evidence confidence: Medium", "The brand has clear entity and service signals, but public corroboration and structured evidence should be improved before stronger claims.", brand["evidence_status"])
    with tabs[1]:
        _ai_visibility(data)
    with tabs[2]:
        _section_card("Recommendation observations", "Recommendation rate uses live or allowed cached observations only. Demo observations are excluded.", "Live")
    with tabs[3]:
        _public_evidence()
    with tabs[4]:
        _competitors()
    with tabs[5]:
        _reports(data)
    with tabs[6]:
        st.line_chart(pd.DataFrame({"Mention rate": [0.46, 0.52, 0.78], "Recommendation rate": [0.31, 0.42, 0.58]}))


def render_audit_workspace() -> None:
    st.set_page_config(page_title="BrandSight GEO", page_icon="GEO", layout="wide", initial_sidebar_state="expanded")
    apply_theme()
    data = _seed_data()
    selected_brand, _date_range, provider = _top_bar(data)
    screen = _sidebar()

    if screen == "Dashboard":
        _dashboard(data, provider)
    elif screen == "New Audit":
        _new_audit()
    elif screen == "Brands":
        _brands(data, selected_brand)
    elif screen == "Competitors":
        _competitors()
    elif screen == "AI Visibility":
        _ai_visibility(data)
    elif screen == "Public Evidence":
        _public_evidence()
    elif screen == "Reports":
        _reports(data)
    elif screen == "Validation Runs":
        _validation_runs(data)
    elif screen == "Settings":
        _settings()
    else:
        _brand_detail(data, selected_brand)
