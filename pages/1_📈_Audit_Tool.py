import streamlit as st
import json
import html
import logging
import os
import re
import hashlib
import plotly.graph_objects as go
from datetime import datetime
from geo_audit_agent.agent import build_geo_audit_agent
from multi_model import run_multi_model_audit

# Import modernized dashboard components
from geo_audit_agent.ui.gap_matrix import render_gap_matrix
from geo_audit_agent.ui.remediation_cards import render_remediation_hub
from geo_audit_agent.ui.lift_simulator import render_lift_simulator
from geo_audit_agent.ui.brand_visibility import render_brand_visibility, normalize_multi_model_results, render_market_simulator
from geo_audit_agent.ui.live_ticker import render_live_ticker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load CSS ---
def load_css(file_name="style.css"):
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_name)
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Page Configuration ---
st.set_page_config(
    page_title="BrandSight GEO • AI-Powered Search Optimization",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom styling
load_css("style.css")

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
    st.session_state.theme = "Light"
if "multi_model_results" not in st.session_state:
    st.session_state.multi_model_results = None
if "tracked_keywords" not in st.session_state:
    st.session_state.tracked_keywords = []
if "keyword_runs" not in st.session_state:
    st.session_state.keyword_runs = {}
if "last_scan_score" not in st.session_state:
    st.session_state.last_scan_score = None

# Pre-populate default data for first-load beauty
if st.session_state.audit_results is None:
    mock_inputs = {
        "brand_name": "Burger Hub",
        "category": "fast food",
        "city": "Islamabad",
        "gaps": [
            {
                "gap_type": "Structured Data",
                "severity": "Critical",
                "description": "Missing schema.org markup (LocalBusiness) on the homepage, preventing search engines from verifying brand entity attributes."
            },
            {
                "gap_type": "Information Gap",
                "severity": "High",
                "description": "Lack of detailed citations regarding ingredient transparency and sourcing in online catalogs."
            }
        ],
        "planned_actions": [],
        "remediation_results": [
            {
                "tool": "JSON-LD Generator",
                "output_full": '{\n  "@context": "https://schema.org",\n  "@type": "Restaurant",\n  "name": "Burger Hub",\n  "address": {\n    "@type": "PostalAddress",\n    "addressLocality": "Islamabad",\n    "addressCountry": "PK"\n  }\n}',
                "output_preview": "JSON-LD Schema for Burger Hub"
            }
        ],
        "confidence_score": 0.68,
        "is_cited": True,
        "llm_response": "Burger Hub has emerging visibility in Islamabad's fast food category. While it is cited in local listings, there is a lack of structured LocalBusiness schema and technical entity backlinks, which creates a critical information gap for generative engines."
    }
    st.session_state.audit_results = mock_inputs
    st.session_state.multi_model_results = run_multi_model_audit("Burger Hub", "fast food", "Islamabad", use_real=False)
    st.session_state.comparison_data["Burger Hub"] = mock_inputs
    st.session_state.remediations = [
        {
            "tool": "JSON-LD Generator",
            "content": mock_inputs["remediation_results"][0]["output_full"],
            "status": "Pending"
        }
    ]
    st.session_state.score_history.append(0.68)

if not st.session_state.tracked_keywords:
    default_keywords = [
        "best fast food in Islamabad",
        "top fast food brands",
        "best burger near me",
        "fast food for delivery",
        "best fast food for families"
    ]
    st.session_state.tracked_keywords = default_keywords
    for i, kw in enumerate(default_keywords):
        st.session_state.keyword_runs[kw] = {
            "last_run": "2026-06-2" + str(2 + (i % 3)),
            "num_runs": 1 + (i % 4)
        }
if st.session_state.multi_model_results:
    st.session_state.multi_model_results = normalize_multi_model_results(st.session_state.multi_model_results)

# --- Custom CSS (Modernized) ---
def apply_theme():
    # Font imports
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    if st.session_state.theme == "Dark":
        bg_style = "radial-gradient(circle at 50% 0%, #1c1140 0%, #0A0A0F 65%, #050508 100%)"
        card_bg = "rgba(26, 26, 46, 0.45)"
        text_color = "#f8fafc"
        border_color = "rgba(255, 255, 255, 0.06)"
        accent_gradient = "linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%)"
        accent_hover = "linear-gradient(135deg, #8B5CF6 0%, #60A5FA 100%)"
        sidebar_bg = "rgba(10, 10, 15, 0.85)"
        input_bg = "rgba(255, 255, 255, 0.03)"
        title_gradient = "linear-gradient(135deg, #ffffff 40%, #a5b4fc 100%)"
        shadow_style = "0 20px 40px -15px rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.05)"
        hover_shadow = "0 20px 40px -10px rgba(124, 58, 237, 0.25), 0 0 0 1px rgba(124, 58, 237, 0.2)"
    else:
        bg_style = "#F8FAFC"
        card_bg = "rgba(255, 255, 255, 0.9)"
        text_color = "#1E293B"
        border_color = "rgba(124, 58, 237, 0.08)"
        accent_gradient = "linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%)"
        accent_hover = "linear-gradient(135deg, #8B5CF6 0%, #60A5FA 100%)"
        sidebar_bg = "linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.98) 100%)"
        input_bg = "rgba(255, 255, 255, 0.9)"
        title_gradient = "linear-gradient(135deg, #7C3AED 0%, #3B82F6 50%, #EC4899 100%)"
        shadow_style = "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 20px 50px -12px rgba(124, 58, 237, 0.12), 0 0 0 1px rgba(255, 255, 255, 0.8) inset"
        hover_shadow = "0 25px 60px -12px rgba(124, 58, 237, 0.2), 0 0 0 1px rgba(124, 58, 237, 0.15)"

    st.markdown(f"""
    <style>
        /* Base styles */
        .stApp {{
            background: {bg_style} !important;
            color: {text_color} !important;
            font-family: 'Inter', sans-serif !important;
        }}

        /* Typography */
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
        }}

        /* Premium Gradient Text for Titles */
        .stApp h1 {{
            background: {title_gradient} !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            display: inline-block !important;
        }}

        /* Metric cards */
        [data-testid="stMetricValue"] {{
            font-family: 'Inter', sans-serif !important;
            font-size: 2.2rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.03em !important;
            background: {accent_gradient} !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
        }}

        .stMetric {{
            background: {card_bg} !important;
            backdrop-filter: blur(20px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
            padding: 24px !important;
            border-radius: 16px !important;
            border: 1px solid {border_color} !important;
            box-shadow: {shadow_style} !important;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }}
        .stMetric:hover {{
            transform: translateY(-4px) !important;
            box-shadow: {hover_shadow} !important;
            border-color: rgba(124, 58, 237, 0.3) !important;
        }}

        /* Containers */
        .custom-card {{
            background: {card_bg} !important;
            backdrop-filter: blur(20px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
            padding: 28px !important;
            border-radius: 16px !important;
            border: 1px solid {border_color} !important;
            box-shadow: {shadow_style} !important;
            margin-bottom: 1.5rem !important;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }}
        .custom-card:hover {{
            transform: translateY(-2px) !important;
            box-shadow: {hover_shadow} !important;
        }}

        /* Buttons */
        .stButton>button {{
            background: {accent_gradient} !important;
            border: none !important;
            color: white !important;
            padding: 10px 24px !important;
            border-radius: 10px !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            letter-spacing: -0.01em !important;
            box-shadow: 0 4px 14px 0 rgba(124, 58, 237, 0.3) !important;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }}
        .stButton>button:hover {{
            background: {accent_hover} !important;
            box-shadow: 0 6px 20px 0 rgba(124, 58, 237, 0.45) !important;
            transform: translateY(-2px) !important;
        }}
        .stButton>button:active {{
            transform: translateY(0px) !important;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px !important;
            background-color: rgba(255, 255, 255, 0.02) !important;
            padding: 6px !important;
            border-radius: 12px !important;
            border: 1px solid {border_color} !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 42px !important;
            background-color: transparent !important;
            border-radius: 8px !important;
            padding: 0 16px !important;
            color: {text_color} !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
            border: none !important;
            transition: all 0.3s !important;
        }}
        .stTabs [aria-selected="true"] {{
            background: {accent_gradient} !important;
            color: white !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.25) !important;
        }}

        /* Gap tiles */
        .gap-tile {{
            padding: 22px !important;
            border-radius: 16px !important;
            margin-bottom: 16px !important;
            background: {card_bg} !important;
            backdrop-filter: blur(20px) !important;
            border: 1px solid {border_color} !important;
            box-shadow: {shadow_style} !important;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }}
        .gap-tile:hover {{
            transform: translateY(-4px) scale(1.02) !important;
            box-shadow: {hover_shadow} !important;
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
            background-color: rgba(10, 10, 20, 0.8) !important;
            border: 1px solid {border_color} !important;
            color: #a5b4fc !important;
            padding: 1.2rem !important;
            border-radius: 12px !important;
            font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
        }}

        /* Scrollbars */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        ::-webkit-scrollbar-thumb {{
            background: rgba(124, 58, 237, 0.3);
            border-radius: 10px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(124, 58, 237, 0.6);
        }}

        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            background: {sidebar_bg} !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border-right: 1px solid {border_color} !important;
        }}

        /* Form containers */
        div[data-testid="stForm"] {{
            background: {card_bg} !important;
            border-radius: 16px !important;
            border: 1px solid {border_color} !important;
            box-shadow: {shadow_style} !important;
            padding: 24px !important;
        }}

        /* Inputs */
        div[data-baseweb="input"] {{
            background-color: {input_bg} !important;
            border-radius: 10px !important;
            border: 1px solid {border_color} !important;
            color: {text_color} !important;
            transition: all 0.3s !important;
        }}
        div[data-baseweb="input"]:focus-within {{
            border-color: rgba(124, 58, 237, 0.6) !important;
            box-shadow: 0 0 0 1px rgba(124, 58, 237, 0.4) !important;
        }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# --- Helper Functions ---
def create_circular_gauge(score, is_dark=True):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        number = {
            'font': {'size': 36, 'color': '#FFFFFF' if is_dark else '#1E293B', 'family': 'Inter'},
            'suffix': '%'
        },
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "rgba(0,0,0,0)", 'tickfont': {'color': 'rgba(0,0,0,0)'}},
            'bar': {'color': "#7C3AED", 'thickness': 0.15},
            'bgcolor': "rgba(124, 58, 237, 0.05)" if not is_dark else "rgba(255, 255, 255, 0.05)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 100], 'color': 'rgba(124, 58, 237, 0.08)' if not is_dark else 'rgba(124, 58, 237, 0.1)'}
            ]
        }
    ))
    fig.update_layout(
        height=140,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def get_competitor_data(brand_name, category):
    import random
    
    category_lower = category.lower()
    
    if "suv" in category_lower or "car" in category_lower or "vehicle" in category_lower or "automotive" in category_lower:
        competitors = ["Mercedes", "BMW", "Lexus", "Audi", "Porsche", "Land Rover", "Cadillac", "Lincoln", "Tesla", "Volvo"]
    elif "food" in category_lower or "burger" in category_lower or "restaurant" in category_lower or "cafe" in category_lower:
        competitors = ["McDonald's", "KFC", "Burger King", "Subway", "Burger Hub", "Pizza Hut", "Hardee's", "Domino's", "Five Guys", "Wendy's"]
    else:
        competitors = [brand_name, "Brand Alpha", "Brand Beta", "Brand Gamma", "Brand Delta", "Brand Epsilon", "Brand Zeta"]
        
    if brand_name not in competitors:
        if len(competitors) > 4:
            competitors[4] = brand_name
        else:
            competitors.append(brand_name)
            
    seen = set()
    competitors = [x for x in competitors if not (x in seen or seen.add(x))]
    
    actual_results = {}

    if st.session_state.multi_model_results and brand_name.lower() == st.session_state.audit_results.get("brand_name", "").lower():
        for r in st.session_state.multi_model_results["results"]:
            actual_results[r["model"]] = int(r["confidence"] * 100) if r["mentioned"] else int(random.Random(r["model"]).randint(15, 35))
            
    model_names = ["ChatGPT", "Gemini", "Meta.ai", "Claude.ai", "DeepSeek"]
    
    data = []
    for b in competitors:
        b_scores = {}
        if b.lower() == brand_name.lower() and actual_results:
            b_scores = actual_results.copy()
        else:
            for m in model_names:
                combined = f"{b}:{m}"
                hash_obj = hashlib.md5(combined.encode())
                seed = int(hash_obj.hexdigest()[:8], 16) % 100
                mentioned = seed % 100 >= 30
                if mentioned:
                    b_scores[m] = 65 + (seed % 31)
                else:
                    b_scores[m] = 15 + (seed % 31)
                    
        b_scores["Average"] = int(sum(b_scores[m] for m in model_names) / len(model_names))
        b_scores["brand"] = b
        data.append(b_scores)

    return data

def get_keyword_monitoring_data(keyword, brand_name):

    model_names = ["ChatGPT", "Gemini", "Meta.ai", "Claude.ai", "DeepSeek"]
    model_breakdown = []
    brands_mentioned_total = 0
    sources_total = 0

    for m in model_names:
        seed_str = f"{keyword}:{m}:{brand_name}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16) % 100

        mentioned = seed % 100 >= 35
        n_brands = 2 + (seed % 12)
        n_sources = 1 + (seed % 9)
        brands_mentioned_total += n_brands
        sources_total += n_sources

        model_breakdown.append({
            "model": m,
            "brand_mentioned": mentioned,
            "brands_count": n_brands,
            "sources_count": n_sources
        })

    overview_seed = int(hashlib.md5(f"{keyword}:overview".encode()).hexdigest()[:8], 16) % 100
    ai_overview = overview_seed % 100 >= 55

    trend = []
    for i in range(6):
        t_seed = int(hashlib.md5(f"{keyword}:trend:{i}".encode()).hexdigest()[:8], 16) % 100
        trend.append(30 + (t_seed % 60))

    return {
        "keyword": keyword,
        "ai_overview": ai_overview,
        "brands_count": brands_mentioned_total,
        "sources_count": sources_total,
        "model_breakdown": model_breakdown,
        "trend": trend
    }

def create_multi_model_chart(data, selected_brand, is_dark=True):
    data_sorted = sorted(data, key=lambda x: x["Average"], reverse=False)
    
    brands = [d["brand"] for d in data_sorted]
    chatgpt_scores = [d["ChatGPT"] for d in data_sorted]
    gemini_scores = [d["Gemini"] for d in data_sorted]
    meta_scores = [d["Meta.ai"] for d in data_sorted]
    claude_scores = [d["Claude.ai"] for d in data_sorted]
    deepseek_scores = [d["DeepSeek"] for d in data_sorted]
    avg_scores = [d["Average"] for d in data_sorted]
    
    fig = go.Figure()
    
    colors = {
        "ChatGPT": "#FF9F43",
        "Gemini": "#EC4899",
        "Meta.ai": "#3B82F6",
        "Claude.ai": "#60A5FA",
        "DeepSeek": "#0D9488",
    }
    
    fig.add_trace(go.Bar(
        y=brands,
        x=chatgpt_scores,
        name="ChatGPT",
        orientation='h',
        marker=dict(
            color=chatgpt_scores,
            colorscale=[[0, "rgba(255, 159, 67, 0.45)"], [1, colors["ChatGPT"]]],
            line=dict(color="rgba(255, 255, 255, 0.25)", width=1)
        ),
        opacity=0.9,
        hovertemplate="<b>%{y}</b><br>ChatGPT: %{x:.1f}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        y=brands,
        x=gemini_scores,
        name="Gemini",
        orientation='h',
        marker=dict(
            color=gemini_scores,
            colorscale=[[0, "rgba(236, 72, 153, 0.45)"], [1, colors["Gemini"]]],
            line=dict(color="rgba(255, 255, 255, 0.25)", width=1)
        ),
        opacity=0.9,
        hovertemplate="<b>%{y}</b><br>Gemini: %{x:.1f}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        y=brands,
        x=meta_scores,
        name="Meta.ai",
        orientation='h',
        marker=dict(
            color=meta_scores,
            colorscale=[[0, "rgba(59, 130, 246, 0.45)"], [1, colors["Meta.ai"]]],
            line=dict(color="rgba(255, 255, 255, 0.25)", width=1)
        ),
        opacity=0.9,
        hovertemplate="<b>%{y}</b><br>Meta.ai: %{x:.1f}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        y=brands,
        x=claude_scores,
        name="Claude.ai",
        orientation='h',
        marker=dict(
            color=claude_scores,
            colorscale=[[0, "rgba(96, 165, 250, 0.45)"], [1, colors["Claude.ai"]]],
            line=dict(color="rgba(255, 255, 255, 0.25)", width=1)
        ),
        opacity=0.9,
        hovertemplate="<b>%{y}</b><br>Claude.ai: %{x:.1f}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        y=brands,
        x=deepseek_scores,
        name="DeepSeek",
        orientation='h',
        marker=dict(
            color=deepseek_scores,
            colorscale=[[0, "rgba(13, 148, 136, 0.45)"], [1, colors["DeepSeek"]]],
            line=dict(color="rgba(255, 255, 255, 0.25)", width=1)
        ),
        opacity=0.9,
        hovertemplate="<b>%{y}</b><br>DeepSeek: %{x:.1f}<extra></extra>"
    ))

    avg_line_color = '#FFFFFF' if is_dark else '#1E293B'
    fig.add_trace(go.Scatter(
        y=brands,
        x=avg_scores,
        name="Average",
        mode='lines+markers',
        line=dict(color=avg_line_color, width=2.5, dash='dash'),
        marker=dict(color='#7C3AED', size=10, line=dict(color=avg_line_color, width=2),
                    symbol='diamond'),
        hovertemplate="<b>%{y}</b><br>Average: %{x:.1f}<extra></extra>"
    ))
    
    selected_brand_normalized = selected_brand.lower()
    brands_lower = [b.lower() for b in brands]
    if selected_brand_normalized in brands_lower:
        selected_idx = brands_lower.index(selected_brand_normalized)
        highlight_fill = "rgba(124, 58, 237, 0.08)" if not is_dark else "rgba(124, 58, 237, 0.12)"
        highlight_border = "rgba(124, 58, 237, 0.3)" if not is_dark else "rgba(124, 58, 237, 0.4)"
        fig.add_shape(
            type="rect",
            xref="paper",
            yref="y",
            x0=0,
            x1=1,
            y0=selected_idx - 0.4,
            y1=selected_idx + 0.4,
            fillcolor=highlight_fill,
            line=dict(color=highlight_border, width=1.5),
            layer="below"
        )
        
    fig.update_layout(
        barmode='group',
        height=500,
        margin=dict(l=120, r=30, t=40, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hoverlabel=dict(
            bgcolor='rgba(255, 255, 255, 0.97)' if not is_dark else 'rgba(26, 26, 46, 0.95)',
            bordercolor='rgba(124, 58, 237, 0.5)',
            font=dict(color='#1E293B' if not is_dark else '#FFFFFF', family='Inter', size=13)
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(color='#94A3B8' if is_dark else '#64748B', size=12)
        ),
        xaxis=dict(
            title=dict(
                text="AI Score",
                font=dict(color='#94A3B8' if is_dark else '#64748B', size=13),
            ),
            tickfont=dict(color='#94A3B8' if is_dark else '#64748B', size=11),
            gridcolor='rgba(255, 255, 255, 0.05)' if is_dark else 'rgba(124, 58, 237, 0.06)',
            range=[0, 105]
        ),
        yaxis=dict(
            tickfont=dict(color='#FFFFFF' if is_dark else '#1E293B', size=13, family='Inter'),
            gridcolor='rgba(0,0,0,0)'
        )
    )
    
    return fig

# --- Helper Functions ---
def create_gauge_chart(score, title="Confidence Score (%)"):
    is_dark = st.session_state.theme == "Dark"
    text_color = 'white' if is_dark else '#1E293B'
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 18, 'color': text_color, 'family': 'Inter'}},
        number = {'font': {'color': text_color, 'family': 'Inter'}, 'suffix': '%'},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#64748B" if not is_dark else "#4A5568"},
            'bar': {'color': "#7C3AED"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 40], 'color': '#FEB2B2'},
                {'range': [40, 70], 'color': '#FBD38D'},
                {'range': [70, 100], 'color': '#9AE6B4'}],
            'threshold': {
                'line': {'color': "white" if is_dark else "#1E293B", 'width': 3},
                'thickness': 0.75,
                'value': score * 100}
        }
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=30, r=30, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white' if is_dark else '#1E293B'}
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
        <div class="geo-shape geo-shape-1"></div>
        <div class="geo-shape geo-shape-2"></div>
        <div class="geo-shape geo-shape-3"></div>
        <div class="geo-shape geo-shape-4"></div>
        <div class="geo-shape geo-shape-5"></div>
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            .main .block-container {
                max-width: 100% !important;
                padding: 0 !important;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
            }
            .stApp {
                background: linear-gradient(135deg, #F8FAFC 0%, #EDE9FE 30%, #DBEAFE 60%, #FCE7F3 100%) !important;
            }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.2, 1.5, 1.2])
    with col2:
        st.markdown("""
            <div class="login-card">
                <div class="login-logo">🌍</div>
                <div class="login-title">BrandSight GEO</div>
                <div class="login-subtitle">AI-Powered Generative Engine Optimization</div>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Sign In", use_container_width=True)

            if submit:
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
            if st.session_state.audit_results:
                st.session_state.last_scan_score = st.session_state.audit_results.get("confidence_score", 0)
            results = agent.invoke(inputs)
            st.session_state.audit_results = results
            st.session_state.comparison_data[brand_name] = results
            
            st.write("⚡ Auditing cross-model visibility (ChatGPT, Gemini, Claude.ai, Meta.ai, DeepSeek)...")
            multi_results = run_multi_model_audit(brand_name, category, city, use_real=False)
            st.session_state.multi_model_results = multi_results

            confidence = results.get("confidence_score", 0.0)
            st.session_state.score_history.append(confidence)
            if len(st.session_state.score_history) > 10:
                st.session_state.score_history.pop(0)

            st.session_state.remediations = []
            for res_item in results.get("remediation_results", []):
                st.session_state.remediations.append({
                    "tool": res_item["tool"],
                    "content": res_item.get("output_full", res_item.get("output_preview", "No preview available")),
                    "status": "Pending"
                })
            status.update(label="✅ Audit Complete!", state="complete", expanded=False)
            st.toast(f"Strategic Audit for {brand_name} finalized.")
        except Exception as e:
            status.update(label="❌ Audit Failed", state="error")
            st.error(f"Execution Error: {e}")
            logger.exception(f"Audit error: {e}")

# --- Main Dashboard ---
if st.session_state.audit_results:
    res = st.session_state.audit_results
    brand_name_val = res.get("brand_name", "Burger Hub")
    category_val = res.get("category", "fast food")
else:
    brand_name_val = "Burger Hub"
    category_val = "fast food"

h_col1, h_col2 = st.columns([3, 1])
with h_col1:
    is_dark_header = st.session_state.theme == "Dark"
    subtitle_color = "#94A3B8" if is_dark_header else "#64748B"
    st.markdown(f"""
        <h1 class='gradient-title' style='margin-bottom: 0;'>AI Brand Index</h1>
        <p style='color: {subtitle_color}; font-size: 1.1rem; margin-top: 5px; font-weight: 500;'>
            {brand_name_val} compared to other brands in {category_val}
        </p>
    """, unsafe_allow_html=True)
with h_col2:
    if st.session_state.audit_results:
        cov_score = st.session_state.multi_model_results['summary']['geo_coverage_score'] if st.session_state.multi_model_results else int(res.get("confidence_score", 0.0) * 100)
        c_g1, c_g2 = st.columns([1, 1.2])
        with c_g1:
            score_label_color = "#94A3B8" if st.session_state.theme == "Dark" else "#64748B"
            st.markdown(f"""
                <div style='text-align: right; padding-top: 25px;'>
                    <span style='font-size: 0.7rem; color: {score_label_color}; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700;'>AI BRAND SCORE</span>
                    <h2 style='font-size: 2.2rem; font-weight: 900; margin: 0; background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>{cov_score}</h2>
                </div>
            """, unsafe_allow_html=True)
        with c_g2:
            st.plotly_chart(create_circular_gauge(cov_score, is_dark=(st.session_state.theme == "Dark")), use_container_width=True, config={'displayModeBar': False})

if st.session_state.audit_results:
    res = st.session_state.audit_results

    tab_overview, tab_gaps, tab_remediation, tab_simulator, tab_compare, tab_keywords, tab_competitors = st.tabs([
        "📈 Dashboard Overview", "🚩 Search Gap Analysis", "🛠️ Remediation Hub", "🧪 What-If Simulator", "🔄 Compare & Benchmark", "🔍 Keyword Monitoring", "🕵️ Competitor Intelligence"
    ])

    with tab_overview:
        m_col1, m_col2, m_col3 = st.columns(3)
        cov_score = st.session_state.multi_model_results['summary']['geo_coverage_score'] if st.session_state.multi_model_results else int(res.get("confidence_score", 0.0) * 100)
        is_dark = st.session_state.theme == "Dark"
        icon_color = "#a5b4fc" if is_dark else "#7C3AED"
        
        with m_col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon-wrapper" style="background: linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%);">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                    </svg>
                </div>
                <div class="metric-info">
                    <div class="metric-label">AI Brand Score</div>
                    <div class="metric-value">{cov_score}</div>
                    <div class="metric-delta delta-success">
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"></polyline></svg>
                        Optimal Presence
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with m_col2:
            is_cited = res.get("is_cited", False)
            status_label = "Cited" if is_cited else "Not Cited"
            status_color = "#10B981" if is_cited else "#EF4444"
            icon_stroke = "#10B981" if is_cited else "#EF4444"
            bg_gradient = "rgba(16, 185, 129, 0.15)" if is_cited else "rgba(239, 68, 68, 0.15)"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon-wrapper" style="background: {bg_gradient}; border-color: rgba(16, 185, 129, 0.3) if is_cited else rgba(239, 68, 68, 0.3); color: {status_color};">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{icon_stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                    </svg>
                </div>
                <div class="metric-info">
                    <div class="metric-label">Citation Status</div>
                    <div class="metric-value" style="color: {status_color}; background: none; -webkit-text-fill-color: {status_color};">{status_label}</div>
                    <div class="metric-delta" style="color: {status_color}; font-weight: 600;">
                        {("Search Success" if is_cited else "Signal Missing")}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with m_col3:
            confidence_pct = int(res.get("confidence_score", 0.0) * 100)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon-wrapper" style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(236, 72, 153, 0.15) 100%);">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="10" rx="2" ry="2"></rect>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                    </svg>
                </div>
                <div class="metric-info">
                    <div class="metric-label">Confidence Score</div>
                    <div class="metric-value">{confidence_pct}%</div>
                    <div class="progress-container">
                        <div class="progress-bar-fill" style="width: {confidence_pct}%;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        render_market_simulator()
        
        col_left, col_right = st.columns([1.6, 1])

        with col_left:
            chart_subtitle_color = "#94A3B8" if is_dark else "#64748B"

            st.markdown(f"""
                <div class="custom-card" style="padding: 28px; margin-bottom: 24px;">
                    <h3 style="margin-top: 0; margin-bottom: 5px; font-size: 1.25rem;">Multi-Model Benchmark Chart</h3>
                    <p style="color: {chart_subtitle_color}; font-size: 0.9rem; margin-top: 0; margin-bottom: 20px;">AI visibility comparison across ChatGPT, Gemini, Meta.ai, Claude.ai, DeepSeek, and Average</p>
                </div>
            """, unsafe_allow_html=True)
            comp_data = get_competitor_data(brand_name_val, category_val)
            fig_multi = create_multi_model_chart(comp_data, brand_name_val, is_dark=(st.session_state.theme == "Dark"))
            st.plotly_chart(fig_multi, use_container_width=True, config={'displayModeBar': False})

            st.markdown("#### 📝 AI Search Intelligence Summary")
            raw_response = html.escape(res.get("llm_response", "No response content."))
            brand_name_val = res.get("brand_name", brand_name)
            highlighted_response = re.sub(
                f"({re.escape(html.escape(brand_name_val))})",
                r'<span style="background-color: #FEEBC8; color: #7B341E; padding: 0 4px; border-radius: 4px; font-weight: 600;">\1</span>',
                raw_response,
                flags=re.IGNORECASE
            )

            theme_bg = "#1A202C" if st.session_state.theme == "Dark" else "rgba(255, 255, 255, 0.9)"
            theme_text = "#E2E8F0" if st.session_state.theme == "Dark" else "#1E293B"
            theme_border = "#2D3748" if st.session_state.theme == "Dark" else "rgba(124, 58, 237, 0.08)"

            st.markdown(f"""
                <div style="max-height: 400px; overflow-y: auto; padding: 20px;
                     background-color: {theme_bg}; color: {theme_text};
                     border-radius: 12px; border: 1px solid {theme_border};
                     line-height: 1.6; font-size: 0.95rem; margin-bottom: 24px;">
                    {highlighted_response}
                </div>
            """, unsafe_allow_html=True)

        with col_right:
            render_brand_visibility(st.session_state.multi_model_results, res.get("confidence_score", 0.0))
            st.markdown("<br>", unsafe_allow_html=True)
            render_live_ticker(brand_name_val)
            st.markdown("<br>", unsafe_allow_html=True)

            pass

        # Define get_bv_trend and rolling_average
        import hashlib
        from datetime import datetime, timedelta

        def get_bv_trend(brand_name, metric_name, n_points=25, base_value=70):
            dates = []
            values = []
            today = datetime.now()
            for i in range(n_points):
                day = today - timedelta(days=(n_points - 1 - i))
                dates.append(day.strftime("%b %d"))
                seed_str = f"{brand_name}:{metric_name}:{i}"
                seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16) % 100
                wobble = (seed % 30) - 15
                values.append(max(5, min(100, base_value + wobble)))
            return dates, values

        def rolling_average(values, window=3):
            avg = []
            for i in range(len(values)):
                start = max(0, i - window + 1)
                chunk = values[start:i + 1]
                avg.append(round(sum(chunk) / len(chunk), 1))
            return avg

        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        trend_col1, trend_col2 = st.columns(2)

        bv_val = int(res.get("confidence_score", 0.0) * 100)
        cr_val = 27 # fallback/default citation rate

        bv_dates, bv_values = get_bv_trend(brand_name_val, "visibility", base_value=int(bv_val))
        cr_dates, cr_values = get_bv_trend(brand_name_val, "citation_rate", base_value=int(cr_val))
        bv_rolling = rolling_average(bv_values)
        cr_rolling = rolling_average(cr_values)

        with trend_col1:
            st.markdown("""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                <span style="font-family: 'Inter', sans-serif; font-size: 1.1rem; font-weight: 700; color: #0F172A;">Brand Visibility Trend</span>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <button style="border: 1px solid #E2E8F0; background: #FFFFFF; border-radius: 6px; padding: 4px 8px; font-size: 0.75rem; color: #64748B; font-weight: 600; cursor: pointer;">+ Add annotation</button>
                    <span style="font-family: 'Inter', sans-serif; font-size: 0.75rem; color: #64748B; font-weight: 600;">Rolling average</span>
                    <div style="width: 28px; height: 16px; background: #7C3AED; border-radius: 8px; position: relative; cursor: pointer; display: inline-block;"><div style="width: 12px; height: 12px; background: white; border-radius: 6px; position: absolute; right: 2px; top: 2px;"></div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            fig_bv_trend = go.Figure()
            fig_bv_trend.add_trace(go.Scatter(
                x=bv_dates, y=bv_values, mode='lines+markers', name='Visibility',
                line=dict(color='#7C3AED', width=3, shape='spline'),
                marker=dict(size=6, color='#7C3AED'),
                fill='tozeroy', fillcolor='rgba(124, 58, 237, 0.05)'
            ))
            fig_bv_trend.add_trace(go.Scatter(
                x=bv_dates, y=bv_rolling, mode='lines', name='Rolling avg',
                line=dict(color='#EC4899', width=2, dash='dash')
            ))
            fig_bv_trend.update_layout(
                height=260,
                margin=dict(l=20, r=20, t=10, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', color='#64748B', size=10),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(124, 58, 237, 0.05)', range=[0, 105]),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                hovermode='x unified'
            )
            st.plotly_chart(fig_bv_trend, use_container_width=True, config={'displayModeBar': False})

        with trend_col2:
            st.markdown("""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                <span style="font-family: 'Inter', sans-serif; font-size: 1.1rem; font-weight: 700; color: #0F172A;">Citation Rate Trend</span>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <button style="border: 1px solid #E2E8F0; background: #FFFFFF; border-radius: 6px; padding: 4px 8px; font-size: 0.75rem; color: #64748B; font-weight: 600; cursor: pointer;">+ Add annotation</button>
                    <span style="font-family: 'Inter', sans-serif; font-size: 0.75rem; color: #64748B; font-weight: 600;">Rolling average</span>
                    <div style="width: 28px; height: 16px; background: #7C3AED; border-radius: 8px; position: relative; cursor: pointer; display: inline-block;"><div style="width: 12px; height: 12px; background: white; border-radius: 6px; position: absolute; right: 2px; top: 2px;"></div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            fig_cr_trend = go.Figure()
            fig_cr_trend.add_trace(go.Scatter(
                x=cr_dates, y=cr_values, mode='lines+markers', name='Citation Rate',
                line=dict(color='#3B82F6', width=3, shape='spline'),
                marker=dict(size=6, color='#3B82F6'),
                fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.05)'
            ))
            fig_cr_trend.add_trace(go.Scatter(
                x=cr_dates, y=cr_rolling, mode='lines', name='Rolling avg',
                line=dict(color='#10B981', width=2, dash='dash')
            ))
            fig_cr_trend.update_layout(
                height=260,
                margin=dict(l=20, r=20, t=10, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', color='#64748B', size=10),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(59, 130, 246, 0.05)', range=[0, 105]),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                hovermode='x unified'
            )
            st.plotly_chart(fig_cr_trend, use_container_width=True, config={'displayModeBar': False})

    with tab_gaps:
        st.subheader("🚩 GEO Search Gap Analysis")
        st.caption("Identify areas where search engines lack clear data or signals about your brand.")
        gaps = res.get("gaps", [])
        if gaps:
            render_gap_matrix(gaps)
            st.divider()
            f_col1, f_col2 = st.columns([2, 1])
            with f_col1:
                gap_types = ["All Categories"] + sorted(list(set([g['gap_type'] for g in gaps])))
                selected_type = st.segmented_control("Filter Perspective", options=gap_types, default="All Categories")

            severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
            display_gaps = [g for g in gaps if selected_type == "All Categories" or g['gap_type'] == selected_type]
            sorted_gaps = sorted(display_gaps, key=lambda x: severity_order.get(x.get('severity', 'Medium').title(), 99))

            st.markdown("#### Detailed Findings")
            for gap in sorted_gaps:
                sev = gap.get('severity', 'Medium').title()
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
            render_remediation_hub(st.session_state.remediations)
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
        current_score = res.get("confidence_score", 0.0)
        gaps = res.get("gaps", [])
        render_lift_simulator(current_score, gaps)

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
                    comp_is_dark = st.session_state.theme == "Dark"
                    fig_comp = go.Figure()
                    comp_colors = ['#7C3AED', '#3B82F6', '#EC4899', '#F59E0B', '#10B981']
                    for idx_b, b in enumerate(selected_brands):
                        b_res = st.session_state.comparison_data[b]
                        fig_comp.add_trace(go.Bar(
                            x=[b],
                            y=[b_res.get('confidence_score', 0.0) * 100],
                            name=b,
                            marker_color=comp_colors[idx_b % len(comp_colors)]
                        ))
                    fig_comp.update_layout(
                        title=dict(text="Search Confidence Benchmark (%)", font=dict(color='white' if comp_is_dark else '#1E293B')),
                        yaxis_range=[0, 105],
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        showlegend=False,
                        font={'color': 'white' if comp_is_dark else '#1E293B'}
                    )
                    st.plotly_chart(fig_comp, use_container_width=True)

                with col_chart2:
                    fig_radar = go.Figure()
                    for b in selected_brands:
                        b_res = st.session_state.comparison_data[b]
                        fig_radar.add_trace(go.Scatterpolar(
                            r=[b_res.get('confidence_score', 0.0)*100,
                               80 if b_res.get('is_cited') else 20,
                               100 - (len(b_res.get('gaps', []))*10)],
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

    with tab_keywords:
        kw_is_dark = st.session_state.theme == "Dark"
        kw_subtitle_color = "#94A3B8" if kw_is_dark else "#64748B"
        st.markdown(f"""
            <h3 style="margin-bottom: 2px;">🔍 Keyword Monitoring</h3>
            <p style="color: {kw_subtitle_color}; font-size: 0.95rem; margin-top: 0; margin-bottom: 20px;">
                Track {brand_name_val}'s visibility across the search queries and prompts AI systems are asked.
            </p>
        """, unsafe_allow_html=True)
        with st.form("add_keyword_form", clear_on_submit=True):
            kw_col1, kw_col2 = st.columns([4, 1])
            with kw_col1:
                new_keyword = st.text_input("Add a keyword or prompt to monitor", placeholder="e.g. best fast food delivery in Islamabad", label_visibility="collapsed")
            with kw_col2:
                add_kw = st.form_submit_button("➕ Add Keyword", use_container_width=True)
            if add_kw and new_keyword.strip():
                kw_clean = new_keyword.strip()
                if kw_clean not in st.session_state.tracked_keywords:
                    st.session_state.tracked_keywords.append(kw_clean)
                    st.session_state.keyword_runs[kw_clean] = {
                        "last_run": datetime.now().strftime("%Y-%m-%d"),
                        "num_runs": 1
                    }
                    st.toast(f"Now monitoring: {kw_clean}")
                    st.rerun()

        if not st.session_state.tracked_keywords:
            st.info("No keywords tracked yet. Add one above to start monitoring AI visibility.")
        else:
            for kw in st.session_state.tracked_keywords:
                kw_meta = st.session_state.keyword_runs.get(kw, {"last_run": "—", "num_runs": 0})
                kw_data = get_keyword_monitoring_data(kw, brand_name_val)
                overview_color = "#10B981" if kw_data["ai_overview"] else "#EF4444"
                overview_bg = "rgba(16, 185, 129, 0.12)" if kw_data["ai_overview"] else "rgba(239, 68, 68, 0.12)"
                overview_label = "YES" if kw_data["ai_overview"] else "NO"

                with st.container(border=True):
                    row_c1, row_c2, row_c3, row_c4, row_c5 = st.columns([3, 1.4, 1, 1, 1])
                    with row_c1:
                        st.markdown(f"**{kw}**")
                        st.caption(f"Last run: {kw_meta['last_run']} · # runs: {kw_meta['num_runs']}")
                    with row_c2:
                        st.markdown(f"""
                            <div style='text-align:center;'>
                                <span class='status-pill' style='background-color: {overview_bg}; color: {overview_color};'>AI Overview: {overview_label}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    with row_c3:
                        st.metric("Brands", kw_data["brands_count"])
                    with row_c4:
                        st.metric("Sources", kw_data["sources_count"])
                    with row_c5:
                        run_now = st.button("🔄 Run", key=f"run_kw_{kw}", use_container_width=True)
                        if run_now:
                            kw_meta["num_runs"] += 1
                            kw_meta["last_run"] = datetime.now().strftime("%Y-%m-%d")
                            st.session_state.keyword_runs[kw] = kw_meta
                            st.toast(f"Re-ran monitoring for: {kw}")
                            st.rerun()

                    with st.expander("📊 View Detail"):
                        d_col1, d_col2 = st.columns([1, 1])
                        with d_col1:
                            st.markdown("**Per-Model Breakdown**")
                            for mb in kw_data["model_breakdown"]:
                                mention_icon = "✅" if mb["brand_mentioned"] else "❌"
                                st.markdown(f"{mention_icon} **{mb['model']}** — {mb['brands_count']} brands, {mb['sources_count']} sources")
                        with d_col2:
                            st.markdown("**Trend Over Time**")
                            fig_kw_trend = go.Figure()
                            fig_kw_trend.add_trace(go.Scatter(
                                y=kw_data["trend"],
                                mode='lines+markers',
                                line=dict(color='#7C3AED', width=3),
                                marker=dict(size=7, color='#3B82F6'),
                                fill='tozeroy',
                                fillcolor='rgba(124, 58, 237, 0.1)'
                            ))
                            fig_kw_trend.update_layout(
                                height=160,
                                margin=dict(l=0, r=0, t=10, b=0),
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                xaxis=dict(showgrid=False, showticklabels=False),
                                yaxis=dict(showgrid=False, showticklabels=False, range=[0, 105]),
                            )
                            st.plotly_chart(fig_kw_trend, use_container_width=True, config={'displayModeBar': False})

    with tab_competitors:
        import time
        import requests
        
        st.markdown("### 🕵️ AI Competitor Intelligence")
        st.caption("Discover, crawl, and analyze how your brand compares to top competitors across AI platforms.")
        
        # Alerts Section
        try:
            user_id = str(res.get("id")) if res.get("id") else "default_user"
            alerts_resp = requests.get(f"http://localhost:8000/api/v1/competitors/alerts/{user_id}").json()
            alerts = alerts_resp.get("alerts", [])
            if alerts:
                with st.expander(f"🔔 You have {len(alerts)} unread alerts!", expanded=True):
                    for alert in alerts:
                        if alert.get("severity") in ["high", "critical"]:
                            st.error(f"**{alert.get('type').upper()}**: {alert.get('message')}")
                        elif alert.get("severity") == "medium":
                            st.warning(f"**{alert.get('type').upper()}**: {alert.get('message')}")
                        else:
                            st.info(f"**{alert.get('type').upper()}**: {alert.get('message')}")
        except Exception:
            pass # Silently fail if alerts API isn't reachable
        
        comp_btn_col, comp_status_col = st.columns([2, 5])
        with comp_btn_col:
            if st.button("🚀 Discover & Analyze Competitors", type="primary", use_container_width=True):
                st.session_state.competitor_task_started = True
                # Call POST /api/v1/competitors/analyze
                try:
                    resp = requests.post("http://localhost:8000/api/v1/competitors/analyze", json={
                        "brand_name": res.get("brand_name", "Burger Hub"),
                        "category": res.get("category", "fast food"),
                        "city": res.get("city", "Islamabad"),
                        "limit": 3
                    })
                    if resp.status_code == 202:
                        st.session_state.competitor_task_id = resp.json().get("task_id")
                except Exception as e:
                    st.error(f"Failed to start task: {e}")
                
        if st.session_state.get("competitor_task_started"):
            task_id = st.session_state.get("competitor_task_id")
            if task_id:
                # Poll status
                try:
                    status_resp = requests.get(f"http://localhost:8000/api/v1/competitors/status/{task_id}").json()
                    status = status_resp.get("status")
                    if status in ["PENDING", "STARTED"]:
                        st.info(f"Analysis task running... Status: {status}")
                        time.sleep(2)
                        st.rerun()
                    elif status == "SUCCESS":
                        st.success("Analysis complete!")
                        st.session_state.competitor_task_started = False
                    elif status == "FAILURE":
                        st.error("Analysis failed.")
                        st.session_state.competitor_task_started = False
                except Exception:
                    st.warning("Could not connect to API for status update.")
            else:
                st.info("Analysis task dispatched. Waiting for task ID...")
        
        # Always attempt to fetch leaderboard
        st.markdown("#### 🏆 AI Visibility Leaderboard")
        brand_name = res.get("brand_name", "Burger Hub")
        try:
            lb_resp = requests.get(f"http://localhost:8000/api/v1/competitors/leaderboard/{brand_name}").json()
            leaderboard = lb_resp.get("leaderboard", [])
            
            if not leaderboard:
                st.info("No competitors analyzed yet. Run a discovery task to populate the leaderboard.")
            else:
                # Render Real Data Table
                html_table = """
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <tr style="background: rgba(124, 58, 237, 0.1); text-align: left;">
                        <th style="padding: 12px; border-bottom: 2px solid #7C3AED;">Rank</th>
                        <th style="padding: 12px; border-bottom: 2px solid #7C3AED;">Brand</th>
                        <th style="padding: 12px; border-bottom: 2px solid #7C3AED;">AI Visibility Score</th>
                    </tr>
                """
                for entry in leaderboard:
                    rank = entry.get("rank")
                    name = entry.get("name")
                    overall = entry.get("overall")
                    color = "#10B981" if rank == 1 else ("#F59E0B" if name.lower() == brand_name.lower() else "#3B82F6")
                    
                    html_table += f"""
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid rgba(0,0,0,0.1);">#{rank}</td>
                        <td style="padding: 12px; border-bottom: 1px solid rgba(0,0,0,0.1);"><b>{name}</b></td>
                        <td style="padding: 12px; border-bottom: 1px solid rgba(0,0,0,0.1);"><span style="color: {color}; font-weight: bold;">{overall}</span></td>
                    </tr>
                    """
                html_table += "</table>"
                st.markdown(html_table, unsafe_allow_html=True)
                
                # Radar Chart
                st.markdown("#### 📊 Dimension Comparison")
                fig = go.Figure()
                dimensions = ["authority", "schema", "content", "reviews", "entities", "citations", "brand"]
                for entry in leaderboard[:3]: # top 3
                    scores = entry.get("scores", {})
                    r_values = [scores.get(d, 0) for d in dimensions]
                    # close the loop
                    r_values.append(r_values[0])
                    theta = dimensions + [dimensions[0]]
                    fig.add_trace(go.Scatterpolar(
                        r=r_values,
                        theta=theta,
                        fill='toself',
                        name=entry.get("name")
                    ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=True,
                    height=400,
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Explanations & Remediation
                st.markdown("#### 🧠 Intelligence & Strategy")
                for entry in leaderboard:
                    if entry.get("name").lower() != brand_name.lower() and entry.get("explanations"):
                        exps = entry.get("explanations")
                        with st.expander(f"Why **{entry.get('name')}** is winning"):
                            st.info(f"**Winning Factors:**\n{exps.get('winning_factors', 'N/A')}")
                            st.warning(f"**Their Strategy:**\n{exps.get('strategy', 'N/A')}")
                            
                            st.markdown("---")
                            st.markdown("##### Was this insight helpful?")
                            fb_col1, fb_col2, _ = st.columns([1, 1, 6])
                            if fb_col1.button("👍 Yes", key=f"up_{entry.get('name')}"):
                                try:
                                    requests.post("http://localhost:8000/api/v1/competitors/feedback", json={
                                        "competitor_id": entry.get("id"),
                                        "is_helpful": True,
                                        "comment": ""
                                    })
                                    st.success("Thanks for your feedback!")
                                except Exception:
                                    pass
                            if fb_col2.button("👎 No", key=f"down_{entry.get('name')}"):
                                try:
                                    requests.post("http://localhost:8000/api/v1/competitors/feedback", json={
                                        "competitor_id": entry.get("id"),
                                        "is_helpful": False,
                                        "comment": ""
                                    })
                                    st.success("Thanks for your feedback!")
                                except Exception:
                                    pass
                            
                            st.markdown("---")
                            # Remediation Button
                            if st.button(f"Generate Remediation for {entry.get('name')}", key=f"rem_{entry.get('name')}"):
                                with st.spinner("Generating JSON-LD and FAQs..."):
                                    try:
                                        rem_resp = requests.post("http://localhost:8000/api/v1/competitors/remediate", json={
                                            "brand_name": brand_name,
                                            "competitor_name": entry.get("name"),
                                            "strategy_text": exps.get("strategy", "")
                                        }).json()
                                        if rem_resp.get("status") == "success":
                                            data = rem_resp.get("data", {})
                                            st.success("Remediation Plan Generated!")
                                            st.markdown("##### Recommended JSON-LD")
                                            st.code(data.get("json_ld", ""), language="json")
                                            st.markdown("##### Recommended FAQs")
                                            for faq in data.get("faqs", []):
                                                st.markdown(f"**Q:** {faq.get('q')}\n\n**A:** {faq.get('a')}")
                                            
                                            # Provide Download
                                            import json
                                            st.download_button(
                                                label="Download Action Plan (JSON)",
                                                data=json.dumps(data, indent=2),
                                                file_name=f"remediation_{entry.get('name')}.json",
                                                mime="application/json"
                                            )
                                        else:
                                            st.error("Failed to generate remediation.")
                                    except Exception as e:
                                        st.error(f"Error connecting to remediation API: {e}")
                                
        except Exception:
            st.warning("Could not fetch leaderboard. Ensure API is running.")

else:
    st.markdown("""
        <div style='text-align: center; padding: 100px 0;'>
            <div style='font-size: 4rem; margin-bottom: 20px; animation: float3D 3s ease-in-out infinite;'>🌍</div>
            <h2 style='font-size: 2.2rem; font-weight: 900; background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 50%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Ready to optimize your brand for AI Search?</h2>
            <p style='color: #64748B; max-width: 600px; margin: 0 auto; font-size: 1.1rem;'>Configure your audit in the sidebar to start identifying and fixing search engine data gaps.</p>
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
        &copy; 2026 Alchemist PANDA
    </div>
""", unsafe_allow_html=True)
