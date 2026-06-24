import streamlit as st
import json
import html
import logging
import os
import re
import plotly.graph_objects as go
from datetime import datetime
from geo_audit_agent.agent import build_geo_audit_agent
from multi_model import run_multi_model_audit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load CSS ---
def load_css(file_name="style.css"):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
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
    st.session_state.theme = "Dark"
if "multi_model_results" not in st.session_state:
    st.session_state.multi_model_results = None

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
        bg_style = "radial-gradient(circle at 50% 0%, #f5f3ff 0%, #f9fafb 70%, #f3f4f6 100%)"
        card_bg = "rgba(255, 255, 255, 0.75)"
        text_color = "#1e293b"
        border_color = "rgba(0, 0, 0, 0.06)"
        accent_gradient = "linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%)"
        accent_hover = "linear-gradient(135deg, #6366F1 0%, #22D3EE 100%)"
        sidebar_bg = "rgba(249, 250, 251, 0.85)"
        input_bg = "rgba(0, 0, 0, 0.02)"
        title_gradient = "linear-gradient(135deg, #0f172a 40%, #312e81 100%)"
        shadow_style = "0 20px 40px -15px rgba(0, 0, 0, 0.05), inset 0 1px 1px rgba(255, 255, 255, 0.8)"
        hover_shadow = "0 20px 40px -10px rgba(79, 70, 229, 0.15), 0 0 0 1px rgba(79, 70, 229, 0.2)"

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
    # score is out of 100
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        number = {
            'font': {'size': 36, 'color': '#FFFFFF' if is_dark else '#0A0A0F', 'family': 'Inter'},
            'suffix': '%'
        },
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "rgba(0,0,0,0)", 'tickfont': {'color': 'rgba(0,0,0,0)'}},
            'bar': {'color': "#7C3AED", 'thickness': 0.15},
            'bgcolor': "rgba(255, 255, 255, 0.05)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 100], 'color': 'rgba(124, 58, 237, 0.1)'}
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
    import hashlib
    import random
    
    # Seed competitor brands based on category
    category_lower = category.lower()
    
    if "suv" in category_lower or "car" in category_lower or "vehicle" in category_lower or "automotive" in category_lower:
        competitors = ["Mercedes", "BMW", "Lexus", "Audi", "Porsche", "Land Rover", "Cadillac", "Lincoln", "Tesla", "Volvo"]
    elif "food" in category_lower or "burger" in category_lower or "restaurant" in category_lower or "cafe" in category_lower:
        competitors = ["McDonald's", "KFC", "Burger King", "Subway", "Burger Hub", "Pizza Hut", "Hardee's", "Domino's", "Five Guys", "Wendy's"]
    else:
        # Generic SaaS or tech/brand competitors
        competitors = [brand_name, "Brand Alpha", "Brand Beta", "Brand Gamma", "Brand Delta", "Brand Epsilon", "Brand Zeta"]
        
    # Ensure brand_name is in the list
    if brand_name not in competitors:
        if len(competitors) > 4:
            competitors[4] = brand_name
        else:
            competitors.append(brand_name)
            
    # Remove duplicates preserving order
    seen = set()
    competitors = [x for x in competitors if not (x in seen or seen.add(x))]
    
    brand_scores = {}
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
            # Generate deterministic scores using hashlib seed
            for m in model_names:
                # Combine brand and model to get a unique seed
                combined = f"{b}:{m}"
                hash_obj = hashlib.md5(combined.encode())
                seed = int(hash_obj.hexdigest()[:8], 16) % 100
                mentioned = seed % 100 >= 30
                if mentioned:
                    # Score between 65 and 95
                    b_scores[m] = 65 + (seed % 31)
                else:
                    # Score between 15 and 45
                    b_scores[m] = 15 + (seed % 31)
                    
        # Calculate Average
        b_scores["Average"] = int(sum(b_scores[m] for m in model_names) / len(model_names))
        b_scores["brand"] = b
        data.append(b_scores)
        
    return data

def create_multi_model_chart(data, selected_brand, is_dark=True):
    # Sort data by Average score descending
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
        "ChatGPT": "#FF9F43",   # Warm Orange
        "Gemini": "#EC4899",    # Vibrant Pink
        "Meta.ai": "#3B82F6",   # Royal Blue
        "Claude.ai": "#60A5FA",  # Light Blue
        "DeepSeek": "#0D9488",  # Deep Teal
    }
    
    # Add grouped horizontal bars
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

    # Add Average line chart overlay
    fig.add_trace(go.Scatter(
        y=brands,
        x=avg_scores,
        name="Average",
        mode='lines+markers',
        line=dict(color='#FFFFFF' if is_dark else '#0A0A0F', width=2, dash='dash'),
        marker=dict(color='#7C3AED', size=8, line=dict(color='#FFFFFF' if is_dark else '#0A0A0F', width=1.5)),
        hovertemplate="<b>%{y}</b><br>Average: %{x:.1f}<extra></extra>"
    ))
    
    # Highlight the selected brand row
    selected_brand_normalized = selected_brand.lower()
    brands_lower = [b.lower() for b in brands]
    if selected_brand_normalized in brands_lower:
        selected_idx = brands_lower.index(selected_brand_normalized)
        fig.add_shape(
            type="rect",
            xref="paper",
            yref="y",
            x0=0,
            x1=1,
            y0=selected_idx - 0.4,
            y1=selected_idx + 0.4,
            fillcolor="rgba(124, 58, 237, 0.12)",
            line=dict(color="rgba(124, 58, 237, 0.4)", width=1),
            layer="below"
        )
        
    fig.update_layout(
        barmode='group',
        height=450,
        margin=dict(l=100, r=20, t=30, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hoverlabel=dict(
            bgcolor='rgba(26, 26, 46, 0.95)' if is_dark else 'rgba(255, 255, 255, 0.95)',
            bordercolor='rgba(124, 58, 237, 0.6)',
            font=dict(color='#FFFFFF' if is_dark else '#0A0A0F', family='Inter', size=12)
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(color='#94A3B8' if is_dark else '#4A5568')
        ),
        xaxis=dict(
            title=dict(
                text="AI Score",
                font=dict(color='#94A3B8' if is_dark else '#4A5568'),
            ),
            tickfont=dict(color='#94A3B8' if is_dark else '#4A5568'),
            gridcolor='rgba(255, 255, 255, 0.05)' if is_dark else 'rgba(0, 0, 0, 0.05)',
            range=[0, 105]
        ),
        yaxis=dict(
            tickfont=dict(color='#FFFFFF' if is_dark else '#0A0A0F', size=12, family='Inter'),
            gridcolor='rgba(0,0,0,0)'
        )
    )
    
    return fig

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
            
            st.write("⚡ Auditing cross-model visibility (ChatGPT, Gemini, Claude.ai, Meta.ai, DeepSeek)...")
            multi_results = run_multi_model_audit(brand_name, category, city, use_real=False)
            st.session_state.multi_model_results = multi_results

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
if st.session_state.audit_results:
    res = st.session_state.audit_results
    brand_name_val = res.get("brand_name", "Burger Hub")
    category_val = res.get("category", "fast food")
else:
    brand_name_val = "Burger Hub"
    category_val = "fast food"

h_col1, h_col2 = st.columns([3, 1])
with h_col1:
    st.markdown(f"""
        <h1 class='gradient-title' style='margin-bottom: 0;'>AI Brand Index</h1>
        <p style='color: #94A3B8; font-size: 1.1rem; margin-top: 5px; font-weight: 500;'>
            {brand_name_val} compared to other brands in {category_val}
        </p>
    """, unsafe_allow_html=True)
with h_col2:
    if st.session_state.audit_results:
        cov_score = st.session_state.multi_model_results['summary']['geo_coverage_score'] if st.session_state.multi_model_results else int(res.get("confidence_score", 0.0) * 100)
        c_g1, c_g2 = st.columns([1, 1.2])
        with c_g1:
            st.markdown(f"""
                <div style='text-align: right; padding-top: 25px;'>
                    <span style='font-size: 0.7rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.1em;'>AI BRAND SCORE</span>
                    <h2 style='font-size: 2.2rem; font-weight: 800; margin: 0; background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>{cov_score}</h2>
                </div>
            """, unsafe_allow_html=True)
        with c_g2:
            st.plotly_chart(create_circular_gauge(cov_score, is_dark=(st.session_state.theme == "Dark")), use_container_width=True, config={'displayModeBar': False})

if st.session_state.audit_results:
    res = st.session_state.audit_results

    # Navigation Tabs
    tab_overview, tab_gaps, tab_remediation, tab_simulator, tab_compare = st.tabs([
        "📈 Dashboard Overview", "🚩 Search Gap Analysis", "🛠️ Remediation Hub", "🧪 What-If Simulator", "🔄 Compare & Benchmark"
    ])

    with tab_overview:
        # Key Metrics Row
        m_col1, m_col2, m_col3 = st.columns(3)
        cov_score = st.session_state.multi_model_results['summary']['geo_coverage_score'] if st.session_state.multi_model_results else int(res.get("confidence_score", 0.0) * 100)
        is_dark = st.session_state.theme == "Dark"
        icon_color = "#a5b4fc" if is_dark else "#4F46E5"
        
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

        # Multi-Model Comparison Chart
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container():
            st.markdown(f"""
                <div class="custom-card" style="padding: 24px; margin-bottom: 24px;">
                    <h3 style="margin-top: 0; margin-bottom: 5px; font-size: 1.25rem;">Multi-Model Benchmark Chart</h3>
                    <p style="color: #94A3B8; font-size: 0.9rem; margin-top: 0; margin-bottom: 20px;">AI visibility comparison across ChatGPT, Gemini, Meta.ai, Claude.ai, DeepSeek, and Average</p>
                </div>
            """, unsafe_allow_html=True)
            comp_data = get_competitor_data(brand_name_val, category_val)
            fig_multi = create_multi_model_chart(comp_data, brand_name_val, is_dark=(st.session_state.theme == "Dark"))
            st.plotly_chart(fig_multi, use_container_width=True, config={'displayModeBar': False})

        # Bottom section: split layout
        col_b1, col_b2 = st.columns([2, 1])
        with col_b1:
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

        with col_b2:
            if st.session_state.score_history:
                st.markdown("#### 📈 Performance Trend")
                # Convert history to values Plotly can use
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(
                    y=[s*100 for s in st.session_state.score_history],
                    mode='lines+markers',
                    line=dict(color='#7C3AED', width=3),
                    marker=dict(size=8, color='#3B82F6'),
                    fill='tozeroy',
                    fillcolor='rgba(124, 58, 237, 0.1)'
                ))
                fig_trend.update_layout(
                    height=240,
                    margin=dict(l=0, r=0, t=10, b=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, showticklabels=False),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255, 255, 255, 0.05)' if is_dark else 'rgba(0, 0, 0, 0.05)', showticklabels=True, range=[0, 105]),
                )
                st.plotly_chart(fig_trend, use_container_width=True)

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
