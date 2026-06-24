import streamlit as st
import plotly.graph_objects as go
import hashlib
import os
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Brand Visibility • BrandSight GEO",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Load shared CSS + page-specific overrides ---
def load_css(file_name="style.css"):
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_name)
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")

# Full-page overrides — remove ALL padding, edge-to-edge
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
    .stApp {
        background: #FFFFFF !important;
    }

    .main .block-container {
        max-width: 100% !important;
        padding: 1.5rem 2.5rem 2rem 2.5rem !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%) !important;
        border-right: 1px solid rgba(124, 58, 237, 0.06) !important;
    }

    /* ===== 3D Metric Cards ===== */
    .bv-metric-card {
        background: #FFFFFF;
        border: 1px solid rgba(0, 0, 0, 0.04);
        border-radius: 20px;
        padding: 28px 24px;
        text-align: center;
        box-shadow:
            0 1px 3px rgba(0, 0, 0, 0.04),
            0 8px 32px rgba(124, 58, 237, 0.08);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        animation: bvCardIn 0.5s ease-out forwards;
        position: relative;
        overflow: hidden;
    }
    .bv-metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        border-radius: 20px 20px 0 0;
    }
    .bv-metric-card:hover {
        transform: translateY(-6px) scale(1.02);
        box-shadow:
            0 20px 60px rgba(124, 58, 237, 0.15),
            0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .bv-metric-card.purple::before { background: linear-gradient(90deg, #7C3AED, #8B5CF6); }
    .bv-metric-card.blue::before { background: linear-gradient(90deg, #3B82F6, #60A5FA); }
    .bv-metric-card.green::before { background: linear-gradient(90deg, #10B981, #34D399); }
    .bv-metric-card.pink::before { background: linear-gradient(90deg, #EC4899, #F472B6); }

    .bv-metric-label {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #94A3B8;
        margin-bottom: 8px;
    }
    .bv-metric-value {
        font-size: 2.8rem;
        font-weight: 900;
        letter-spacing: -0.04em;
        line-height: 1;
        margin-bottom: 6px;
    }
    .bv-metric-value.purple { color: #7C3AED; }
    .bv-metric-value.blue { color: #3B82F6; }
    .bv-metric-value.green { color: #10B981; }
    .bv-metric-value.pink { color: #EC4899; }

    .bv-metric-delta {
        font-size: 0.8rem;
        font-weight: 600;
    }
    .bv-delta-up { color: #10B981; }
    .bv-delta-down { color: #EF4444; }
    .bv-delta-neutral { color: #94A3B8; }

    /* ===== Platform Progress Bars ===== */
    .platform-row {
        display: flex;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid rgba(0, 0, 0, 0.03);
    }
    .platform-row:last-child { border-bottom: none; }

    .platform-name {
        width: 140px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #1E293B;
        flex-shrink: 0;
    }
    .platform-bar-container {
        flex: 1;
        height: 28px;
        background: #F1F5F9;
        border-radius: 14px;
        overflow: hidden;
        margin: 0 16px;
        position: relative;
    }
    .platform-bar-fill {
        height: 100%;
        border-radius: 14px;
        transition: width 1s cubic-bezier(0.16, 1, 0.3, 1);
        display: flex;
        align-items: center;
        padding-left: 12px;
    }
    .platform-bar-fill span {
        font-size: 0.75rem;
        font-weight: 700;
        color: white;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    .platform-pct {
        width: 45px;
        text-align: right;
        font-size: 0.9rem;
        font-weight: 700;
        flex-shrink: 0;
    }

    /* ===== Section Cards ===== */
    .bv-section {
        background: #FFFFFF;
        border: 1px solid rgba(0, 0, 0, 0.04);
        border-radius: 20px;
        padding: 28px;
        box-shadow:
            0 1px 3px rgba(0, 0, 0, 0.03),
            0 8px 32px rgba(124, 58, 237, 0.06);
        margin-bottom: 24px;
        animation: bvCardIn 0.6s ease-out forwards;
    }
    .bv-section:hover {
        box-shadow:
            0 12px 40px rgba(124, 58, 237, 0.1),
            0 1px 3px rgba(0, 0, 0, 0.03);
    }
    .bv-section-title {
        font-size: 1.1rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 4px;
        letter-spacing: -0.02em;
    }
    .bv-section-subtitle {
        font-size: 0.8rem;
        color: #94A3B8;
        margin-bottom: 20px;
    }

    /* ===== Keyword Table Header ===== */
    .kw-table-header {
        display: grid;
        grid-template-columns: 2.5fr 1fr 1.4fr 1.2fr 1.2fr 1.2fr;
        align-items: end;
        padding: 0 16px 12px 16px;
        border-bottom: 2px solid #E2E8F0;
        margin-bottom: 4px;
    }
    .kw-col-header {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748B;
        text-align: center;
    }
    .kw-col-header:first-child { text-align: left; }

    .kw-platform-header {
        text-align: center;
        padding: 6px 12px;
        border-radius: 8px;
        color: white;
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .kw-platform-header.google { background: linear-gradient(135deg, #F59E0B, #F97316); }
    .kw-platform-header.chatgpt { background: linear-gradient(135deg, #10B981, #059669); }
    .kw-platform-header.perplexity { background: linear-gradient(135deg, #3B82F6, #2563EB); }
    .kw-platform-header.claude { background: linear-gradient(135deg, #8B5CF6, #7C3AED); }
    .kw-platform-header.gemini { background: linear-gradient(135deg, #EC4899, #DB2777); }

    /* ===== Keyword Rows ===== */
    .kw-row {
        display: grid;
        grid-template-columns: 2.5fr 1fr 1.4fr 1.2fr 1.2fr 1.2fr;
        align-items: center;
        padding: 16px;
        border-bottom: 1px solid rgba(0, 0, 0, 0.03);
        transition: all 0.2s ease;
    }
    .kw-row:hover {
        background: rgba(124, 58, 237, 0.02);
    }
    .kw-keyword {
        font-size: 0.95rem;
        font-weight: 600;
        color: #3B82F6;
    }
    .kw-meta {
        font-size: 0.75rem;
        color: #94A3B8;
        margin-top: 2px;
    }
    .kw-cell {
        text-align: center;
        font-size: 1rem;
        font-weight: 700;
    }
    .kw-cell.brands { color: #7C3AED; }
    .kw-cell.sources { color: #3B82F6; }

    .kw-pill {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kw-pill.yes {
        background: rgba(16, 185, 129, 0.12);
        color: #059669;
    }
    .kw-pill.no {
        background: rgba(239, 68, 68, 0.12);
        color: #EF4444;
    }

    @keyframes bvCardIn {
        from {
            opacity: 0;
            transform: translateY(16px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
</style>
""", unsafe_allow_html=True)


# ── Session state ──
if "bv_brand" not in st.session_state:
    st.session_state.bv_brand = "Burger Hub"
if "bv_category" not in st.session_state:
    st.session_state.bv_category = "fast food"
if "bv_city" not in st.session_state:
    st.session_state.bv_city = "Islamabad"
if "bv_keywords" not in st.session_state:
    st.session_state.bv_keywords = []
if "bv_keyword_data" not in st.session_state:
    st.session_state.bv_keyword_data = {}


# ── Data generators (deterministic, hashlib-seeded) ──

def _seed(text):
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16)

PLATFORMS = [
    ("Google AI Overview", "#F59E0B", "#FEF3C7"),
    ("ChatGPT",           "#10B981", "#D1FAE5"),
    ("Perplexity",        "#3B82F6", "#DBEAFE"),
    ("Claude.ai",         "#7C3AED", "#EDE9FE"),
    ("Gemini",            "#EC4899", "#FCE7F3"),
    ("Meta.ai",           "#6366F1", "#E0E7FF"),
    ("DeepSeek",          "#0D9488", "#CCFBF1"),
    ("Bing Copilot",      "#2563EB", "#DBEAFE"),
    ("You.com",           "#D946EF", "#FAE8FF"),
    ("Brave Search AI",   "#F97316", "#FFEDD5"),
]

def generate_platform_scores(brand, category):
    scores = {}
    for name, _, _ in PLATFORMS:
        s = _seed(f"{brand}:{category}:{name}")
        scores[name] = 10 + (s % 86)
    return scores

def generate_keyword_row(keyword, brand):
    s = _seed(f"{keyword}:{brand}")
    models = ["Google", "ChatGPT", "Perplexity", "Claude.ai", "Gemini"]
    row = {"keyword": keyword}

    # Google columns
    row["ai_overview"] = (s % 100) >= 50
    row["google_brands"] = s % 15
    row["google_sources"] = (s * 3) % 12

    # ChatGPT
    s2 = _seed(f"{keyword}:chatgpt:{brand}")
    row["chatgpt_brands"] = 1 + (s2 % 14)

    # Perplexity
    s3 = _seed(f"{keyword}:perplexity:{brand}")
    row["perplexity_brands"] = 1 + (s3 % 12)
    row["perplexity_sources"] = 1 + (s3 % 5)

    # Claude
    s4 = _seed(f"{keyword}:claude:{brand}")
    row["claude_brands"] = 1 + (s4 % 11)

    # Gemini
    s5 = _seed(f"{keyword}:gemini:{brand}")
    row["gemini_brands"] = 1 + (s5 % 13)

    # Meta
    row["last_run"] = datetime.now() - timedelta(days=s % 5)
    row["num_runs"] = 1 + (s % 6)

    return row

def generate_trend_data(brand, category, metric_name, n_points=14):
    points = []
    for i in range(n_points):
        s = _seed(f"{brand}:{category}:{metric_name}:{i}")
        base = 30 + (s % 50)
        points.append(base)
    return points

def compute_visibility_score(platform_scores):
    vals = list(platform_scores.values())
    return int(sum(vals) / len(vals)) if vals else 0

def compute_citation_rate(brand, category):
    s = _seed(f"{brand}:{category}:citation")
    return 20 + (s % 55)

def compute_sentiment(brand, category):
    s = _seed(f"{brand}:{category}:sentiment")
    return 40 + (s % 50)


# ── Sidebar ──
with st.sidebar:
    st.markdown("## 📊 Brand Visibility")
    st.caption("AI Search Monitoring Dashboard")
    st.divider()

    st.markdown("#### Configuration")
    st.session_state.bv_brand = st.text_input("Brand Name", value=st.session_state.bv_brand)
    st.session_state.bv_category = st.text_input("Category", value=st.session_state.bv_category)
    st.session_state.bv_city = st.text_input("City", value=st.session_state.bv_city)

    st.divider()
    st.markdown("""
    <div style='font-size: 0.75rem; color: #94A3B8;'>
        <b>BrandSight GEO v1.2</b><br>
        Engine: LangGraph Orchestrator<br>
        &copy; 2026 Alchemist PANDA
    </div>
    """, unsafe_allow_html=True)


brand = st.session_state.bv_brand
category = st.session_state.bv_category

# ── Page Header ──
st.markdown(f"""
<div style="margin-bottom: 8px;">
    <h1 style="font-size: 2.8rem; font-weight: 900; margin-bottom: 0;
        background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 50%, #EC4899 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        display: inline-block; letter-spacing: -0.04em;">
        📊 Brand Visibility Dashboard
    </h1>
    <p style="color: #64748B; font-size: 1.05rem; margin-top: 4px;">
        Full-spectrum AI search monitoring for <b style="color: #7C3AED;">{brand}</b> in <b>{category}</b>
    </p>
</div>
""", unsafe_allow_html=True)

# ── Data ──
platform_scores = generate_platform_scores(brand, category)
bv_score = compute_visibility_score(platform_scores)
citation_rate = compute_citation_rate(brand, category)
sentiment = compute_sentiment(brand, category)

# ── TOP SECTION: Metrics + Platforms ──
left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    # Row 1: Three metric cards
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.markdown(f"""
        <div class="bv-metric-card purple">
            <div class="bv-metric-label">Brand Visibility</div>
            <div class="bv-metric-value purple">{bv_score}%</div>
            <div class="bv-metric-delta bv-delta-up">&#9650; +3.2% vs last week</div>
        </div>
        """, unsafe_allow_html=True)
    with mc2:
        st.markdown(f"""
        <div class="bv-metric-card blue">
            <div class="bv-metric-label">Citation Rate</div>
            <div class="bv-metric-value blue">{citation_rate}%</div>
            <div class="bv-metric-delta bv-delta-up">&#9650; +1.8% vs last week</div>
        </div>
        """, unsafe_allow_html=True)
    with mc3:
        sent_delta_class = "bv-delta-up" if sentiment >= 50 else "bv-delta-down"
        st.markdown(f"""
        <div class="bv-metric-card green">
            <div class="bv-metric-label">Sentiment Score</div>
            <div class="bv-metric-value green">{sentiment}%</div>
            <div class="bv-metric-delta {sent_delta_class}">&#9650; Positive trend</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Row 2: Platform breakdown with progress bars
    st.markdown("""
    <div class="bv-section">
        <div class="bv-section-title">Platform Breakdown</div>
        <div class="bv-section-subtitle">Visibility score per AI search platform (0 – 100)</div>
    """, unsafe_allow_html=True)

    bar_html = ""
    for name, color, _ in PLATFORMS:
        pct = platform_scores[name]
        if pct >= 80:
            bar_color = f"linear-gradient(90deg, #10B981, #34D399)"
        elif pct >= 60:
            bar_color = f"linear-gradient(90deg, #F59E0B, #FBBF24)"
        elif pct >= 40:
            bar_color = f"linear-gradient(90deg, #F97316, #FB923C)"
        else:
            bar_color = f"linear-gradient(90deg, #EF4444, #F87171)"

        pct_color = "#10B981" if pct >= 80 else "#F59E0B" if pct >= 60 else "#F97316" if pct >= 40 else "#EF4444"

        bar_html += f"""
        <div class="platform-row">
            <div class="platform-name">{name}</div>
            <div class="platform-bar-container">
                <div class="platform-bar-fill" style="width: {pct}%; background: {bar_color};">
                    <span>{pct}</span>
                </div>
            </div>
            <div class="platform-pct" style="color: {pct_color};">{pct}%</div>
        </div>
        """

    bar_html += "</div>"
    st.markdown(bar_html, unsafe_allow_html=True)

with right_col:
    # Row 1: Brand Visibility Trend
    st.markdown("""
    <div class="bv-section">
        <div class="bv-section-title">Brand Visibility Trend</div>
        <div class="bv-section-subtitle">14-day rolling visibility score across all platforms</div>
    </div>
    """, unsafe_allow_html=True)

    trend_bv = generate_trend_data(brand, category, "visibility")
    dates = [(datetime.now() - timedelta(days=13 - i)).strftime("%b %d") for i in range(14)]

    fig_bv = go.Figure()
    fig_bv.add_trace(go.Scatter(
        x=dates, y=trend_bv, mode='lines+markers',
        line=dict(color='#7C3AED', width=3, shape='spline'),
        marker=dict(size=7, color='#7C3AED', line=dict(color='white', width=2)),
        fill='tozeroy',
        fillcolor='rgba(124, 58, 237, 0.06)',
        hovertemplate="<b>%{x}</b><br>Visibility: %{y}%<extra></extra>"
    ))
    # Rolling average
    rolling = [sum(trend_bv[max(0,i-2):i+1])/len(trend_bv[max(0,i-2):i+1]) for i in range(len(trend_bv))]
    fig_bv.add_trace(go.Scatter(
        x=dates, y=rolling, mode='lines',
        line=dict(color='#EC4899', width=2, dash='dash'),
        name='3-day avg',
        hovertemplate="<b>%{x}</b><br>Avg: %{y:.1f}%<extra></extra>"
    ))
    fig_bv.update_layout(
        height=220, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color='#94A3B8')),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.04)', range=[0, 105],
                   tickfont=dict(size=10, color='#94A3B8')),
        showlegend=False,
        hoverlabel=dict(bgcolor='white', bordercolor='#7C3AED',
                        font=dict(color='#1E293B', family='Inter', size=12))
    )
    st.plotly_chart(fig_bv, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Row 2: Citation Rate Trend
    st.markdown("""
    <div class="bv-section">
        <div class="bv-section-title">Citation Rate Trend</div>
        <div class="bv-section-subtitle">14-day citation frequency in AI-generated responses</div>
    </div>
    """, unsafe_allow_html=True)

    trend_cr = generate_trend_data(brand, category, "citation")

    fig_cr = go.Figure()
    fig_cr.add_trace(go.Scatter(
        x=dates, y=trend_cr, mode='lines+markers',
        line=dict(color='#3B82F6', width=3, shape='spline'),
        marker=dict(size=7, color='#3B82F6', line=dict(color='white', width=2)),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.06)',
        hovertemplate="<b>%{x}</b><br>Citation Rate: %{y}%<extra></extra>"
    ))
    rolling_cr = [sum(trend_cr[max(0,i-2):i+1])/len(trend_cr[max(0,i-2):i+1]) for i in range(len(trend_cr))]
    fig_cr.add_trace(go.Scatter(
        x=dates, y=rolling_cr, mode='lines',
        line=dict(color='#10B981', width=2, dash='dash'),
        name='3-day avg',
        hovertemplate="<b>%{x}</b><br>Avg: %{y:.1f}%<extra></extra>"
    ))
    fig_cr.update_layout(
        height=220, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color='#94A3B8')),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.04)', range=[0, 105],
                   tickfont=dict(size=10, color='#94A3B8')),
        showlegend=False,
        hoverlabel=dict(bgcolor='white', bordercolor='#3B82F6',
                        font=dict(color='#1E293B', family='Inter', size=12))
    )
    st.plotly_chart(fig_cr, use_container_width=True, config={'displayModeBar': False})


# ── DIVIDER ──
st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
st.divider()

# ── BOTTOM SECTION: Keyword Monitoring Table (Otterly.ai style) ──
st.markdown(f"""
<div style="margin-bottom: 4px;">
    <h2 style="font-size: 1.6rem; font-weight: 900; color: #0F172A; letter-spacing: -0.03em; margin-bottom: 2px;">
        🔍 Keyword / Prompt Monitoring
    </h2>
    <p style="color: #64748B; font-size: 0.9rem; margin-top: 0;">
        Track how <b style="color:#7C3AED;">{brand}</b> appears across AI search platforms for key queries
    </p>
</div>
""", unsafe_allow_html=True)

# Add keyword
with st.form("bv_add_kw", clear_on_submit=True):
    akc1, akc2 = st.columns([5, 1])
    with akc1:
        new_kw = st.text_input("Add keyword", placeholder=f"e.g. best {category} in {st.session_state.bv_city}", label_visibility="collapsed")
    with akc2:
        add_btn = st.form_submit_button("➕ Add Keyword", use_container_width=True)
    if add_btn and new_kw.strip():
        kw_clean = new_kw.strip()
        if kw_clean not in st.session_state.bv_keywords:
            st.session_state.bv_keywords.append(kw_clean)
            st.toast(f"Tracking: {kw_clean}")
            st.rerun()

# Default keywords
if not st.session_state.bv_keywords:
    st.session_state.bv_keywords = [
        f"best {category} in {st.session_state.bv_city}",
        f"best {category} brands",
        f"top {category} restaurants",
        f"what are the top {category} brands",
        f"best {category} for delivery",
        f"best {category} for families",
    ]

# Table header (Otterly.ai style with colored platform headers)
st.markdown("""
<div style="margin-top: 12px;">
    <div class="kw-table-header">
        <div>
            <div class="kw-col-header" style="text-align: left;">Keywords / Prompts</div>
        </div>
        <div>
            <div class="kw-col-header">Last Run</div>
        </div>
        <div style="text-align: center;">
            <div class="kw-platform-header google">Google</div>
            <div style="display: flex; gap: 4px; justify-content: center;">
                <div class="kw-col-header" style="flex:1;">AI-Overviews</div>
                <div class="kw-col-header" style="flex:1;"># brands</div>
                <div class="kw-col-header" style="flex:1;"># sources</div>
            </div>
        </div>
        <div style="text-align: center;">
            <div class="kw-platform-header chatgpt">ChatGPT</div>
            <div class="kw-col-header"># brands</div>
        </div>
        <div style="text-align: center;">
            <div class="kw-platform-header perplexity">Perplexity</div>
            <div style="display: flex; gap: 4px; justify-content: center;">
                <div class="kw-col-header" style="flex:1;"># brands</div>
                <div class="kw-col-header" style="flex:1;"># sources</div>
            </div>
        </div>
        <div style="text-align: center;">
            <div class="kw-platform-header claude">Claude</div>
            <div class="kw-col-header"># brands</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Keyword rows (rendered as Streamlit containers for interactive Run buttons)
for kw in st.session_state.bv_keywords:
    row = generate_keyword_row(kw, brand)
    pill_class = "yes" if row["ai_overview"] else "no"
    pill_text = "YES" if row["ai_overview"] else "NO"

    with st.container(border=False):
        c1, c2, c3, c4, c5, c6, c7, c8, c9, c10 = st.columns(
            [2.5, 1, 0.7, 0.6, 0.6, 0.7, 0.6, 0.6, 0.7, 0.5]
        )
        with c1:
            st.markdown(f"<span style='font-weight:600; color:#3B82F6; font-size:0.95rem;'>{kw}</span><br><span style='font-size:0.75rem; color:#94A3B8;'>{row['last_run'].strftime('%Y-%m-%d')} &middot; # runs: {row['num_runs']}</span>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div style='text-align:center; padding-top:8px;'><span class='kw-pill {pill_class}'>{pill_text}</span></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div style='text-align:center; padding-top:6px; font-size:1.1rem; font-weight:700; color:#F59E0B;'>{row['google_brands']}</div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div style='text-align:center; padding-top:6px; font-size:1.1rem; font-weight:700; color:#F97316;'>{row['google_sources']}</div>", unsafe_allow_html=True)
        with c5:
            st.markdown(f"<div style='text-align:center; padding-top:6px; font-size:1.1rem; font-weight:700; color:#10B981;'>{row['chatgpt_brands']}</div>", unsafe_allow_html=True)
        with c6:
            st.markdown(f"<div style='text-align:center; padding-top:6px; font-size:1.1rem; font-weight:700; color:#3B82F6;'>{row['perplexity_brands']}</div>", unsafe_allow_html=True)
        with c7:
            st.markdown(f"<div style='text-align:center; padding-top:6px; font-size:1.1rem; font-weight:700; color:#2563EB;'>{row['perplexity_sources']}</div>", unsafe_allow_html=True)
        with c8:
            st.markdown(f"<div style='text-align:center; padding-top:6px; font-size:1.1rem; font-weight:700; color:#7C3AED;'>{row['claude_brands']}</div>", unsafe_allow_html=True)
        with c9:
            st.markdown(f"<div style='text-align:center; padding-top:6px; font-size:1.1rem; font-weight:700; color:#EC4899;'>{row['gemini_brands']}</div>", unsafe_allow_html=True)
        with c10:
            if st.button("🔄", key=f"bv_run_{kw}", help="Re-run monitoring"):
                st.toast(f"Re-ran: {kw}")
                st.rerun()

        with st.expander("📊 View Detail"):
            dc1, dc2 = st.columns([1, 1])
            with dc1:
                st.markdown("**Per-Platform Results**")
                platforms_detail = [
                    ("Google AI Overview", "YES" if row["ai_overview"] else "NO", row["google_brands"], row["google_sources"]),
                    ("ChatGPT", "—", row["chatgpt_brands"], "—"),
                    ("Perplexity", "—", row["perplexity_brands"], row["perplexity_sources"]),
                    ("Claude.ai", "—", row["claude_brands"], "—"),
                    ("Gemini", "—", row["gemini_brands"], "—"),
                ]
                for pname, aio, nb, ns in platforms_detail:
                    cols_d = st.columns([2, 1, 1, 1])
                    cols_d[0].write(f"**{pname}**")
                    cols_d[1].write(f"AI: {aio}")
                    cols_d[2].write(f"Brands: {nb}")
                    cols_d[3].write(f"Sources: {ns}")

            with dc2:
                st.markdown("**Trend**")
                s_trend = _seed(f"{kw}:trend")
                trend_vals = [25 + (_seed(f"{kw}:t:{i}") % 65) for i in range(8)]
                fig_detail = go.Figure()
                fig_detail.add_trace(go.Scatter(
                    y=trend_vals, mode='lines+markers',
                    line=dict(color='#7C3AED', width=2.5, shape='spline'),
                    marker=dict(size=6, color='#3B82F6'),
                    fill='tozeroy', fillcolor='rgba(124, 58, 237, 0.06)'
                ))
                fig_detail.update_layout(
                    height=150, margin=dict(l=0, r=0, t=5, b=0),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, showticklabels=False),
                    yaxis=dict(showgrid=False, showticklabels=False, range=[0, 105]),
                )
                st.plotly_chart(fig_detail, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='border-bottom: 1px solid rgba(0,0,0,0.04);'></div>", unsafe_allow_html=True)
