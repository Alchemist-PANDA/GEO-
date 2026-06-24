import streamlit as st
import json
import html
import logging
import os
import re
import plotly.graph_objects as go
from datetime import datetime
from geo_audit_agent.agent import build_geo_audit_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Page Configuration ---
st.set_page_config(
    page_title="BrandSight GEO • AI-Powered Search Optimization",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Initialization ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "audit_results" not in st.session_state:
    st.session_state.audit_results = None
if "remediations" not in st.session_state:
    st.session_state.remediations = []
if "score_history" not in st.session_state:
    st.session_state.score_history = []
if "comparison_data" not in st.session_state:
    st.session_state.comparison_data = {}
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

# --- Custom CSS (Modernized) ---
def apply_theme():
    if st.session_state.theme == "Dark":
        bg_color = "#0e1117"
        card_color = "#1d232a"
        text_color = "#e2e8f0"
        border_color = "#2d3748"
        accent_color = "#3b82f6"
    else:
        bg_color = "#f7fafc"
        card_color = "#ffffff"
        text_color = "#2d3748"
        border_color = "#e2e8f0"
        accent_color = "#3182ce"

    st.markdown(f"""
    <style>
        /* Base styles */
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
            font-family: 'Inter', sans-serif;
        }}

        /* Metric cards */
        [data-testid="stMetricValue"] {{
            font-size: 1.8rem;
            font-weight: 700;
        }}

        .stMetric {{
            background-color: {card_color};
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border: 1px solid {border_color};
            transition: transform 0.2s ease;
        }}
        .stMetric:hover {{
            transform: translateY(-2px);
        }}

        /* Containers */
        .custom-card {{
            background-color: {card_color};
            padding: 24px;
            border-radius: 12px;
            border: 1px solid {border_color};
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }}

        /* Buttons */
        .stButton>button {{
            border-radius: 8px;
            padding: 0.5rem 1rem;
            transition: all 0.2s;
            font-weight: 500;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: transparent;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 45px;
            white-space: pre;
            background-color: {card_color};
            border-radius: 8px 8px 0 0;
            padding: 0 20px;
            border: 1px solid {border_color};
            color: {text_color};
            font-weight: 600;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {accent_color} !important;
            color: white !important;
            border-color: {accent_color} !important;
        }}

        /* Gap tiles */
        .gap-tile {{
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 12px;
            border-left: 6px solid;
            background-color: {card_color};
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid {border_color};
            border-left-width: 6px;
        }}
        .gap-tile:hover {{
            transform: scale(1.02);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }}

        /* Status labels */
        .status-pill {{
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        /* Code blocks */
        code {{
            background-color: #1a202c !important;
            color: #e2e8f0 !important;
            padding: 1rem !important;
            border-radius: 8px !important;
            font-size: 0.9rem !important;
        }}

        /* Scrollbars */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: {bg_color};
        }}
        ::-webkit-scrollbar-thumb {{
            background: {border_color};
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: {accent_color};
        }}

        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            background-color: {card_color};
            border-right: 1px solid {border_color};
        }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# --- Helper Functions ---
def create_gauge_chart(score, title="Confidence Score (%)"):
    is_dark = st.session_state.theme == "Dark"
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 18, 'color': 'white' if is_dark else '#2D3748', 'family': 'Inter'}},
        number = {'font': {'color': 'white' if is_dark else '#2D3748', 'family': 'Inter'}, 'suffix': '%'},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#4A5568"},
            'bar': {'color': "#3182ce"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 40], 'color': '#FEB2B2'},
                {'range': [40, 70], 'color': '#FBD38D'},
                {'range': [70, 100], 'color': '#9AE6B4'}],
            'threshold': {
                'line': {'color': "white" if is_dark else "#2D3748", 'width': 3},
                'thickness': 0.75,
                'value': score * 100}
        }
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=30, r=30, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white' if is_dark else '#2D3748'}
    )
    return fig

def generate_markdown_report(res, approved_items):
    report = f"# BrandSight GEO Audit Report - {res['brand_name']}\n"
    report += f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    report += "## Executive Summary\n"
    report += f"- **Confidence Score:** {res.get('confidence_score', 0.0):.2f}/1.00\n"
    report += f"- **Citation Status:** {'Cited' if res.get('is_cited', False) else 'Not Cited'}\n"
    report += f"- **Identified Gaps:** {len(res.get('gaps', []))}\n\n"

    report += "## Detailed Analysis\n"
    report += res.get('llm_response', 'No analysis available.') + "\n\n"

    report += "## Identified Gaps\n"
    for gap in res.get('gaps', []):
        report += f"### {gap['gap_type']} ({gap['severity']})\n"
        report += f"{gap['description']}\n\n"

    if approved_items:
        report += "## Approved Remediations\n"
        for item in approved_items:
            report += f"### Tool: {item['tool']}\n"
            report += "```\n" + item['content'] + "\n```\n\n"

    report += "\n---\n*Report generated by BrandSight GEO Dashboard.*"
    return report

# --- Authentication ---
def login_screen():
    st.markdown("""
        <div style='text-align: center; padding-top: 50px;'>
            <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>🌍 BrandSight GEO</h1>
            <p style='color: #718096; margin-bottom: 2rem;'>AI-Powered Generative Engine Optimization Dashboard</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.markdown("### Secure Login")
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="admin")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Sign In", use_container_width=True)

                if submit:
                    # Issue #2: credentials from env vars with backward-compatible defaults
                    expected_user = os.getenv("DASHBOARD_USER", "admin")
                    expected_pass = os.getenv("DASHBOARD_PASS", "geo123")
                    if username == expected_user and password == expected_pass:
                        st.session_state.authenticated = True
                        st.success("Welcome back!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

if not st.session_state.authenticated:
    login_screen()
    st.stop()

# --- Sidebar Inputs ---
with st.sidebar:
    st.markdown("## 🌍 BrandSight GEO")
    st.caption("Generative Engine Optimization")
    st.divider()

    # Theme Toggle with Tooltip
    st.markdown("#### Display Settings")
    st.session_state.theme = st.radio(
        "Dashboard Mode",
        options=["Light", "Dark"],
        index=0 if st.session_state.theme == "Light" else 1,
        horizontal=True,
        help="Switch between light and dark visual modes."
    )

    st.divider()
    st.markdown("#### Audit Configuration")

    with st.form("audit_form"):
        brand_name = st.text_input("Brand Name", value="Burger Hub", help="The name of the brand to audit.")
        category = st.text_input("Category", value="fast food", placeholder="e.g. coffee shop, tech startup")
        city = st.text_input("City", value="Islamabad", placeholder="e.g. New York, London")

        run_audit = st.form_submit_button("🚀 Launch GEO Audit", use_container_width=True)

if run_audit:
    with st.status(f"Conducting GEO Audit: {brand_name} in {city}", expanded=True) as status:
        try:
            st.write("🔄 Initializing BrandSight Intelligence Engine...")
            agent = build_geo_audit_agent()
            inputs = {
                "brand_name": brand_name,
                "category": category,
                "city": city,
                "gaps": [],
                "planned_actions": [],
                "remediation_results": []
            }
            st.write(f"🌐 Crawling search engines for {brand_name} visibility...")
            results = agent.invoke(inputs)
            st.session_state.audit_results = results
            st.session_state.comparison_data[brand_name] = results

            # Update history
            confidence = results.get("confidence_score", 0.0)
            st.session_state.score_history.append(confidence)
            if len(st.session_state.score_history) > 10:
                st.session_state.score_history.pop(0)

            # Initialize remediations state
            st.session_state.remediations = []
            for res_item in results.get("remediation_results", []):
                st.session_state.remediations.append({
                    "tool": res_item["tool"],
                    # Issue #15: use full output if available, fall back to preview
                    "content": res_item.get("output_full", res_item.get("output_preview", "No preview available")),
                    "status": "Pending"
                })
            status.update(label="✅ Audit Complete!", state="complete", expanded=False)
            st.toast(f"Strategic Audit for {brand_name} finalized.")
        except Exception as e:
            status.update(label="❌ Audit Failed", state="error")
            st.error(f"Execution Error: {e}")
            logger.exception(f"Audit error: {e}")  # Issue #17: preserve traceback

# --- Main Dashboard ---
# Header
h_col1, h_col2 = st.columns([2, 1])
with h_col1:
    st.title("📊 GEO Strategy Dashboard")
    st.caption("Intelligence-driven Search Optimization & Remediation Hub")
with h_col2:
    if st.session_state.audit_results:
        st.markdown(f"""
            <div style='text-align: right; padding-top: 10px;'>
                <span class='status-pill' style='background-color: #9AE6B4; color: #22543d;'>Live Intelligence</span>
                <p style='font-size: 0.8rem; color: #718096; margin-top: 5px;'>Last Sync: {datetime.now().strftime('%H:%M:%S')}</p>
            </div>
        """, unsafe_allow_html=True)

if st.session_state.audit_results:
    res = st.session_state.audit_results

    # Navigation Tabs
    tab_overview, tab_gaps, tab_remediation, tab_simulator, tab_compare = st.tabs([
        "📈 Dashboard Overview", "🚩 Search Gap Analysis", "🛠️ Remediation Hub", "🧪 What-If Simulator", "🔄 Compare & Benchmark"
    ])

    with tab_overview:
        col_main, col_sidebar = st.columns([2, 1])

        with col_sidebar:
            with st.container(border=True):
                st.markdown("#### Performance Score")
                confidence = res.get("confidence_score", 0.0)
                st.plotly_chart(create_gauge_chart(confidence), use_container_width=True)

                if st.session_state.score_history:
                    st.divider()
                    st.markdown("#### Performance Trend")
                    # Convert history to values Plotly can use
                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Scatter(
                        y=[s*100 for s in st.session_state.score_history],
                        mode='lines+markers',
                        line=dict(color='#3182ce', width=3),
                        marker=dict(size=8, color='#3182ce'),
                        fill='tozeroy',
                        fillcolor='rgba(49, 130, 206, 0.1)'
                    ))
                    fig_trend.update_layout(
                        height=150,
                        margin=dict(l=0, r=0, t=10, b=0),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(showgrid=False, showticklabels=False),
                        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', showticklabels=True, range=[0, 105]),
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)

        with col_main:
            # Metrics Row
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                is_cited = res.get("is_cited", False)
                label = "Cited" if is_cited else "Uncited"
                color = "normal" if is_cited else "inverse"
                st.metric("Citation Index", label, delta="Search Success" if is_cited else "Signal Missing", delta_color=color)
            with m_col2:
                gaps_count = len(res.get("gaps", []))
                st.metric("Critical Gaps", gaps_count, delta=f"{gaps_count} risks", delta_color="inverse")
            with m_col3:
                sentiment = "Positive" # Existing logic placeholder
                st.metric("AI Sentiment", sentiment, delta="Favorable")

            # Analysis Summary Card
            st.markdown("#### 📝 AI Search Intelligence Summary")
            # Issue #3: HTML-escape LLM output before injection to prevent XSS
            raw_response = html.escape(res.get("llm_response", "No response content."))
            brand_name_val = res.get("brand_name", brand_name)
            highlighted_response = re.sub(
                f"({re.escape(html.escape(brand_name_val))})",
                r'<span style="background-color: #FEEBC8; color: #7B341E; padding: 0 4px; border-radius: 4px; font-weight: 600;">\1</span>',
                raw_response,
                flags=re.IGNORECASE
            )

            theme_bg = "#1A202C" if st.session_state.theme == "Dark" else "#FFFFFF"
            theme_text = "#E2E8F0" if st.session_state.theme == "Dark" else "#2D3748"
            theme_border = "#2D3748" if st.session_state.theme == "Dark" else "#E2E8F0"

            st.markdown(f"""
                <div style="max-height: 400px; overflow-y: auto; padding: 20px;
                     background-color: {theme_bg}; color: {theme_text};
                     border-radius: 12px; border: 1px solid {theme_border};
                     line-height: 1.6; font-size: 0.95rem;">
                    {highlighted_response}
                </div>
            """, unsafe_allow_html=True)

    with tab_gaps:
        st.subheader("🚩 GEO Search Gap Analysis")
        st.caption("Identify areas where search engines lack clear data or signals about your brand.")

        gaps = res.get("gaps", [])

        if gaps:
            # Filtering and Ordering
            f_col1, f_col2 = st.columns([2, 1])
            with f_col1:
                gap_types = ["All Categories"] + sorted(list(set([g['gap_type'] for g in gaps])))
                selected_type = st.segmented_control("Filter Perspective", options=gap_types, default="All Categories")

            severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
            display_gaps = [g for g in gaps if selected_type == "All Categories" or g['gap_type'] == selected_type]
            # Issue #11: normalize severity to title-case for display
            sorted_gaps = sorted(display_gaps, key=lambda x: severity_order.get(x.get('severity', 'Medium').title(), 99))

            # Heatmap Visual
            st.divider()
            cols = st.columns(4)
            for idx, gap in enumerate(sorted_gaps):
                sev = gap.get('severity', 'Medium').title()  # Issue #11: normalize
                color = {"Critical": "#E53E3E", "High": "#DD6B20", "Medium": "#3182CE", "Low": "#38A169"}.get(sev, "#718096")

                with cols[idx % 4]:
                    st.markdown(f"""
                    <div class="gap-tile" style="border-left-color: {color};">
                        <div style="font-weight: bold; color: {color}; font-size: 0.75rem; letter-spacing: 0.05em; text-transform: uppercase;">{sev} RISK</div>
                        <div style="font-weight: 700; margin: 4px 0; font-size: 1rem;">{gap['gap_type']}</div>
                        <div style="font-size: 0.85rem; color: #718096; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.4;">{gap['description']}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Details List
            st.markdown("#### Detailed Findings")
            for gap in sorted_gaps:
                sev = gap.get('severity', 'Medium').title()  # Issue #11: normalize
                color_class = {"Critical": "red", "High": "orange", "Medium": "blue", "Low": "green"}.get(sev, "gray")
                with st.expander(f"**{gap['gap_type']}** — :{color_class}[{sev} Priority]"):
                    st.write(gap['description'])
                    c1, c2, _ = st.columns([1, 1, 2])
                    with c1:
                        if st.button("Fix in Hub", key=f"fix_nav_{gap['gap_type']}"):
                            st.info("Direct implementation strategy generated in Remediation Hub.")
                    with c2:
                        st.button("Explain Impact", key=f"exp_{gap['gap_type']}", help="AI explanation of why this gap affects your SEO.")
        else:
            st.success("✨ Zero critical gaps identified! Your brand data satisfies search engine requirements.")

    with tab_remediation:
        st.subheader("🛠️ Remediation Hub")
        st.caption("Execute AI-generated fixes to bridge data gaps and improve search visibility.")

        if st.session_state.remediations:
            for idx, item in enumerate(st.session_state.remediations):
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"### `{item['tool']}` Strategy")
                    with c2:
                        status = item['status']
                        color_hex = "#38A169" if status == "Approved" else "#E53E3E" if status == "Rejected" else "#DD6B20"
                        st.markdown(f"<div style='text-align: right;'><span class='status-pill' style='background-color: {color_hex}22; color: {color_hex};'>{status}</span></div>", unsafe_allow_html=True)

                    tab_code, tab_preview = st.tabs(["💻 Implementation Code", "📝 Human-Readable Preview"])

                    with tab_code:
                        edited_content = st.text_area(
                            "Edit Remediation Snippet",
                            value=item['content'],
                            height=250,
                            key=f"edit_code_{idx}"
                        )
                        st.session_state.remediations[idx]['content'] = edited_content
                        st.code(edited_content, language="json" if "JSON" in item['tool'] else "markdown")

                    with tab_preview:
                        st.markdown(edited_content)

                    # Action Bar
                    st.divider()
                    b_col1, b_col2, b_col3, b_col4 = st.columns([1, 1, 1, 2])
                    with b_col1:
                        if st.button("✅ Approve", key=f"app_btn_{idx}", use_container_width=True):
                            st.session_state.remediations[idx]['status'] = "Approved"
                            st.toast(f"Approved {item['tool']}")
                            st.rerun()
                    with b_col2:
                        if st.button("❌ Reject", key=f"rej_btn_{idx}", use_container_width=True):
                            st.session_state.remediations[idx]['status'] = "Rejected"
                            st.toast(f"Rejected {item['tool']}")
                            st.rerun()
                    with b_col3:
                        st.download_button(
                            "📥 Download",
                            data=edited_content,
                            file_name=f"brandsight_{item['tool'].lower().replace(' ', '_')}.txt",
                            key=f"dl_btn_{idx}",
                            use_container_width=True
                        )
                    with b_col4:
                        if st.button("✨ Auto-Optimize", key=f"opt_{idx}", help="AI refinement of this content."):
                            st.warning("Auto-optimization is a premium feature.")

            # Bulk Actions
            st.markdown("#### 🚀 Deployment Package")
            approved_items = [i for i in st.session_state.remediations if i['status'] == "Approved"]

            pkg_col1, pkg_col2 = st.columns(2)
            with pkg_col1:
                if approved_items:
                    export_data = {
                        "brand": res["brand_name"],
                        "timestamp": datetime.now().isoformat(),
                        "audit_score": res.get("confidence_score", 0.0),
                        "approved_remediations": approved_items
                    }
                    st.download_button(
                        label="📦 Export All Approved Assets (JSON)",
                        data=json.dumps(export_data, indent=4),
                        file_name=f"geo_package_{res['brand_name'].lower()}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                else:
                    st.button("📦 Export All Approved Assets (JSON)", disabled=True, use_container_width=True)

            with pkg_col2:
                report_md = generate_markdown_report(res, approved_items)
                st.download_button(
                    # Issue #26: label accurately reflects the actual output format
                    label="📄 Download Audit Report (Markdown)",
                    data=report_md,
                    file_name=f"geo_report_{res['brand_name'].lower()}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    help="Downloads a Markdown report."
                )
        else:
            st.info("Run an audit to generate remediation strategies.")

    with tab_simulator:
        st.subheader("🧪 Strategic Lift Simulator")
        st.caption("Visualize your projected visibility improvements after implementing remediations.")

        current_score = res.get("confidence_score", 0.0)
        gaps = res.get("gaps", [])

        if gaps:
            col_controls, col_visual = st.columns([1.2, 1])

            with col_controls:
                st.markdown("#### Remediation Roadmap")
                st.write("Toggle the items you plan to implement:")
                fixed_gaps = []
                for i, gap in enumerate(gaps):
                    with st.container(border=True):
                        c_check, c_label = st.columns([1, 8])
                        with c_check:
                            if st.checkbox("", key=f"sim_check_{i}"):
                                fixed_gaps.append(gap)
                        with c_label:
                            st.markdown(f"**{gap['gap_type']}**")
                            st.caption(f"Priority: {gap['severity']}")

            with col_visual:
                # Simulation Math (Client-side only)
                severity_weights = {"Critical": 0.15, "High": 0.10, "Medium": 0.05, "Low": 0.02}
                raw_lift = sum([severity_weights.get(g['severity'], 0.05) for g in fixed_gaps])
                diminishing_return_factor = (1.0 - current_score)
                lift = raw_lift * diminishing_return_factor
                predicted_score = min(1.0, current_score + lift)

                st.plotly_chart(create_gauge_chart(predicted_score, title="Projected GEO Score (%)"), use_container_width=True)

                s_col1, s_col2 = st.columns(2)
                with s_col1:
                    st.metric("Current", f"{current_score*100:.0f}%")
                with s_col2:
                    st.metric("Projected", f"{predicted_score*100:.0f}%", delta=f"{lift*100:+.1f}%")

                st.success(f"**Growth Opportunity:** Implementing these fixes could bridge your search presence gap by **{lift*100:.1f} points**.")
        else:
            st.balloons()
            st.success("Your brand performance is already optimized for Generative Search.")

    with tab_compare:
        st.subheader("🔄 Market Benchmarking")
        if len(st.session_state.comparison_data) < 1:
            st.info("Run audits for competing brands to unlock market comparisons.")
        else:
            brands = list(st.session_state.comparison_data.keys())
            selected_brands = st.multiselect("Select Brands to Benchmark", options=brands, default=brands[:2])

            if len(selected_brands) >= 1:
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    fig_comp = go.Figure()
                    for b in selected_brands:
                        b_res = st.session_state.comparison_data[b]
                        fig_comp.add_trace(go.Bar(
                            x=[b],
                            y=[b_res.get('confidence_score', 0.0) * 100],
                            name=b,
                            marker_color='#3182ce' if b == brand_name else '#A0AEC0'
                        ))
                    fig_comp.update_layout(
                        title="Search Confidence Benchmark (%)",
                        yaxis_range=[0, 105],
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        showlegend=False,
                        font={'color': 'white' if st.session_state.theme == "Dark" else '#2D3748'}
                    )
                    st.plotly_chart(fig_comp, use_container_width=True)

                with col_chart2:
                    fig_radar = go.Figure()
                    # Simulating some dimensions for a radar chart
                    for b in selected_brands:
                        b_res = st.session_state.comparison_data[b]
                        fig_radar.add_trace(go.Scatterpolar(
                            r=[b_res.get('confidence_score', 0.0)*100,
                               80 if b_res.get('is_cited') else 20,
                               100 - (len(b_res.get('gaps', []))*10)],
                            # Issue #25: removed placeholder dimensions that had hardcoded values
                            theta=['Search Presence', 'Citations', 'Data Completeness'],
                            fill='toself',
                            name=b
                        ))
                    fig_radar.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        showlegend=True,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        height=350,
                        margin=dict(l=40, r=40, t=20, b=20)
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)

else:
    # Empty State Content
    st.markdown("""
        <div style='text-align: center; padding: 100px 0;'>
            <h2 style='font-size: 2rem;'>Ready to optimize your brand for AI Search?</h2>
            <p style='color: #718096; max-width: 600px; margin: 0 auto;'>Configure your audit in the sidebar to start identifying and fixing search engine data gaps.</p>
        </div>
    """, unsafe_allow_html=True)

    col_feat1, col_feat2, col_feat3 = st.columns(3)
    with col_feat1:
        with st.container(border=True):
            st.markdown("#### 🔍 Multi-Agent Audit")
            st.caption("Deep search across ChatGPT, Gemini, and Perplexity to identify how AI perceives your brand.")
    with col_feat2:
        with st.container(border=True):
            st.markdown("#### 🛠️ Smart Remediation")
            st.caption("Automated generation of JSON-LD, content schemas, and SEO data to bridge intelligence gaps.")
    with col_feat3:
        with st.container(border=True):
            st.markdown("#### 📈 Benchmarking")
            st.caption("Compare your GEO performance against competitors and market standards.")

# Footer
st.sidebar.divider()
st.sidebar.markdown("""
    <div style='font-size: 0.75rem; color: #718096;'>
        <b>BrandSight GEO v1.2</b><br>
        Engine: LangGraph Orchestrator<br>
        © 2026 Alchemist PANDA
    </div>
""", unsafe_allow_html=True)
