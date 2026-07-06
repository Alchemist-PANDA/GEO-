import streamlit as st

# --- DEBUGGING PRINTS ---
print("[DEBUG] => Starting execution of dashboard.py")

if "render_count" not in st.session_state:
    st.session_state.render_count = 0
st.session_state.render_count += 1
print(f"[DEBUG] => Render count: {st.session_state.render_count}")

import textwrap
import logging
import os
import hashlib
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- NEW AUTH IMPORTS ---
from auth import current_user, sign_in, sign_up, sign_out

print("[DEBUG] => Auth imports completed")

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

# st.warning(f"🔧 Debug Mode | Render Loop Counter: {st.session_state.render_count}")
print("[DEBUG] => Page config and initial warning displayed")

# --- Load custom styling for the dashboard (used later) ---
def load_css(file_name="style.css"):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ==============================================
# BRANDSIGHT GEO LOGIN PAGE (shown if user is not logged in)
# ==============================================

def render_brandsight_login():
    # Inject Bloom CSS (liquid glass, fonts, layout)
    st.markdown(textwrap.dedent("""
    <style>
        /* ----- Fonts ----- */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Source+Serif+4:ital,wght@0,400;1,500&display=swap');

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        /* Video background */
        #bloom-bg-video {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            object-fit: cover;
            z-index: 0;
        }

        .bloom-content {
            position: relative;
            z-index: 10;
            min-height: 100vh;
            display: flex;
            align-items: stretch;
            font-family: 'Poppins', sans-serif;
        }

        /* Liquid Glass classes */
        .liquid-glass {
            position: relative;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.01);
            background-blend-mode: luminosity;
            backdrop-filter: blur(4px);
            border: none;
            box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.1);
            border-radius: 1.5rem;
        }
        .liquid-glass::before {
            content: '';
            position: absolute;
            inset: 0;
            padding: 1.4px;
            background: linear-gradient(180deg, rgba(255,255,255,0.45) 0%, rgba(255,255,255,0.15) 20%, transparent 40%, transparent 60%, rgba(255,255,255,0.15) 80%, rgba(255,255,255,0.45) 100%);
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            mask-composite: exclude;
            -webkit-mask-composite: xor;
            pointer-events: none;
            border-radius: inherit;
        }

        .liquid-glass-strong {
            position: relative;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.01);
            background-blend-mode: luminosity;
            backdrop-filter: blur(50px);
            border: none;
            box-shadow: 4px 4px 4px rgba(0,0,0,0.05), inset 0 1px 1px rgba(255,255,255,0.15);
            border-radius: 1.5rem;
        }
        .liquid-glass-strong::before {
            content: '';
            position: absolute;
            inset: 0;
            padding: 1.4px;
            background: linear-gradient(180deg, rgba(255,255,255,0.5) 0%, rgba(255,255,255,0.2) 20%, transparent 40%, transparent 60%, rgba(255,255,255,0.2) 80%, rgba(255,255,255,0.5) 100%);
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            mask-composite: exclude;
            -webkit-mask-composite: xor;
            pointer-events: none;
            border-radius: inherit;
        }

        .serif-italic {
            font-family: 'Source Serif 4', serif;
            font-style: italic;
            font-weight: 500;
        }

        .text-white\\/80 { color: rgba(255,255,255,0.8); }
        .text-white\\/60 { color: rgba(255,255,255,0.6); }
        .text-white\\/50 { color: rgba(255,255,255,0.5); }
        .bg-white\\/15 { background-color: rgba(255,255,255,0.15); }

        .brandsight-left-panel {
            position: relative;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        .brandsight-left-panel .glass-overlay {
            position: absolute;
            inset: 1.5rem;
            border-radius: 1.5rem;
        }
        @media (min-width: 1024px) {
            .brandsight-left-panel .glass-overlay { inset: 1.5rem; }
        }
        .brandsight-hero {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            gap: 1.5rem;
            padding: 2rem 0;
        }
        @media (min-width: 1024px) {
            .brandsight-hero { align-items: flex-start; text-align: left; }
        }

        /* Hide Streamlit branding on login page */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header { visibility: hidden; }
        .stApp > header { display: none; }
    </style>
    """), unsafe_allow_html=True)

    # --- Video Background ---
    st.markdown(textwrap.dedent("""
    <video id="bloom-bg-video" autoplay loop muted playsinline>
        <source src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260315_073750_51473149-4350-4920-ae24-c8214286f323.mp4" type="video/mp4" />
    </video>
    """), unsafe_allow_html=True)

    # --- Two-panel layout using Streamlit columns ---
    col_left, col_right = st.columns([0.52, 0.48], gap="large")

    # ----- LEFT PANEL (Hero) -----
    with col_left:
        st.markdown(textwrap.dedent("""
        <div class="brandsight-left-panel">
            <div class="glass-overlay liquid-glass-strong"></div>
            <div style="position:relative; z-index:20; display:flex; flex-direction:column; height:100%; padding: 0.5rem 1rem;">
                <!-- Nav -->
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="display:flex; align-items:center; gap:0.5rem;">
                        <span style="font-size:1.75rem;">🌍</span>
                        <span style="font-size:1.5rem; font-weight:600; letter-spacing:-0.05em; color:white;">BrandSight GEO</span>
                    </div>
                    <div class="liquid-glass" style="padding:0.5rem 1.5rem; border-radius:9999px; cursor:default;">
                        <span style="color:rgba(255,255,255,0.8); font-size:0.875rem;">Menu</span>
                    </div>
                </div>
                <!-- Hero -->
                <div class="brandsight-hero">
                    <span style="font-size:3.5rem;">🌍</span>
                    <h1 style="font-size:3.5rem; font-weight:500; letter-spacing:-0.05em; line-height:1.2; color:white; margin:0;">
                        Innovating the <br />
                        <span class="serif-italic text-white/80">spirit of AI search</span>
                    </h1>
                    <div style="display:flex; gap:0.75rem; flex-wrap:wrap; justify-content:center;">
                        <div class="liquid-glass" style="padding:0.4rem 1.25rem; border-radius:9999px; color:rgba(255,255,255,0.8); font-size:0.75rem;">Generative Engine Optimization</div>
                        <div class="liquid-glass" style="padding:0.4rem 1.25rem; border-radius:9999px; color:rgba(255,255,255,0.8); font-size:0.75rem;">Brand Visibility</div>
                        <div class="liquid-glass" style="padding:0.4rem 1.25rem; border-radius:9999px; color:rgba(255,255,255,0.8); font-size:0.75rem;">AI Audits</div>
                    </div>
                    <div style="margin-top:1rem; max-width:28rem;">
                        <div style="font-size:0.7rem; letter-spacing:0.1em; text-transform:uppercase; color:rgba(255,255,255,0.5); margin-bottom:0.25rem;">VISIONARY DESIGN</div>
                        <div style="font-size:1.2rem; font-weight:500; color:white;">
                            "We imagined a realm <span class="serif-italic text-white/80">with no ending.</span>"
                        </div>
                        <div style="display:flex; align-items:center; gap:1rem; margin-top:0.75rem;">
                            <hr style="flex:1; border:0; height:1px; background:rgba(255,255,255,0.2);" />
                            <span style="font-size:0.7rem; letter-spacing:0.1em; color:rgba(255,255,255,0.5);">MARCUS AURELIO</span>
                            <hr style="flex:1; border:0; height:1px; background:rgba(255,255,255,0.2);" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """), unsafe_allow_html=True)

    # ----- RIGHT PANEL (Login/Signup) -----
    with col_right:
        st.markdown(textwrap.dedent("""
        <div style="display:flex; flex-direction:column; justify-content:center; align-items:center; min-height:100vh; padding:1.5rem 0.5rem;">
            <div class="liquid-glass-strong" style="width:100%; max-width:400px; padding:2rem 1.5rem; border-radius:1.5rem; text-align:center;">
                <h2 style="color:white; font-weight:500; margin-top:0; margin-bottom:0.5rem;">Welcome to BrandSight GEO</h2>
                <p style="color:rgba(255,255,255,0.6); font-size:0.9rem; margin-bottom:1.5rem;">Sign in to access your GEO dashboard</p>
        """), unsafe_allow_html=True)

        # --- Streamlit Auth Forms ---
        tab_login, tab_signup = st.tabs(["Log in", "Create account"])

        with tab_login:
            with st.form("brandsight_login_form", clear_on_submit=False):
                login_email = st.text_input("Email", placeholder="you@example.com", key="brandsight_login_email")
                login_password = st.text_input("Password", type="password", placeholder="••••••••", key="brandsight_login_pass")
                submitted_login = st.form_submit_button("Log in", use_container_width=True)
                if submitted_login:
                    if login_email and login_password:
                        ok, msg = sign_in(login_email, login_password)
                        if ok:
                            st.success("Logged in! Redirecting...")
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please enter both email and password.")

        with tab_signup:
            with st.form("brandsight_signup_form", clear_on_submit=False):
                signup_email = st.text_input("Email", placeholder="you@example.com", key="brandsight_signup_email")
                signup_password = st.text_input("Password", type="password", placeholder="min 8 characters", key="brandsight_signup_pass")
                submitted_signup = st.form_submit_button("Create account", use_container_width=True)
                if submitted_signup:
                    if signup_email and signup_password:
                        if len(signup_password) < 8:
                            st.error("Password must be at least 8 characters.")
                        else:
                            ok, msg = sign_up(signup_email, signup_password)
                            if ok:
                                st.success("Account created! Check your email to confirm.")
                            else:
                                st.error(msg)
                    else:
                        st.warning("Please fill in all fields.")

        st.markdown(textwrap.dedent("""
                <p style="color:rgba(255,255,255,0.4); font-size:0.7rem; margin-top:1rem;">Secured by Supabase Auth • RLS enforced</p>
            </div>
        </div>
        """), unsafe_allow_html=True)

# ==============================================
# DASHBOARD (shown only when user is logged in)
# ==============================================

# Check authentication status
user = current_user()

if user is None:
    # Show BrandSight GEO login page
    render_brandsight_login()
    # Stop execution here so the dashboard doesn't render
    st.stop()

# --- If we reach here, the user is logged in ---
print("[DEBUG] => User is logged in, proceeding to render dashboard")
# Load dashboard CSS and proceed with the normal dashboard
load_css("style.css")

# --- Session State Initialization ---
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
    from multi_model import run_multi_model_audit
    st.session_state.multi_model_results = run_multi_model_audit("Burger Hub", "fast food", "Islamabad", use_real=False, user_id=st.session_state.get("user_id"))
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


# --- Custom CSS (Modernized) ---
def apply_theme():
    # Font imports
    st.markdown(textwrap.dedent("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    """), unsafe_allow_html=True)

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
def clean_html(html_str: str) -> str:
    return "\n".join(line.strip() for line in html_str.split("\n"))

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
                combined = f"{b}:{m}"
                hash_obj = hashlib.md5(combined.encode())
                seed = int(hash_obj.hexdigest()[:8], 16) % 100
                mentioned = seed % 100 >= 30
                if mentioned:
                    b_scores[m] = 65 + (seed % 31)
                else:
                    b_scores[m] = 15 + (seed % 31)
                    
        # Calculate Average
        b_scores["Average"] = int(sum(b_scores[m] for m in model_names) / len(model_names))
        b_scores["brand"] = b
        data.append(b_scores)

    return data

def get_keyword_monitoring_data(keyword, brand_name):
    """Restructure multi-model audit signals by keyword/prompt instead of by brand."""
    import hashlib

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

    # Deterministic trend (last 6 runs) for the sparkline view
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


BV_PLATFORMS = [
    "DeepSeek", "Mistral", "Claude", "Grok", "Gemini",
    "ChatGPT", "Google AI Mode", "Google AI Overview", "Perplexity", "Copilot"
]


def _bv_seed(text):
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16)


def get_bv_platform_scores(brand_name):
    """Deterministic per-platform visibility score (0-100) for the Brand Visibility tab."""
    scores = []
    for platform in BV_PLATFORMS:
        seed = _bv_seed(f"{brand_name}:bv:{platform}") % 100
        score = 25 + (seed % 70)
        scores.append({"platform": platform, "score": score})
    return sorted(scores, key=lambda x: x["score"], reverse=True)


def get_bv_metrics(brand_name, platform_scores):
    """Top-line Brand Visibility, Citation Rate and Sentiment metrics with deltas."""
    visibility = sum(p["score"] for p in platform_scores) / len(platform_scores)
    cr_seed = _bv_seed(f"{brand_name}:citation_rate") % 100
    citation_rate = 10 + (cr_seed % 35)
    sent_seed = _bv_seed(f"{brand_name}:sentiment") % 100
    sentiment = 55 + (sent_seed % 40)

    def _delta(text):
        d = (_bv_seed(text) % 20) / 10.0 - 1.0
        return round(d, 1)

    return {
        "visibility": round(visibility, 1),
        "visibility_delta": _delta(f"{brand_name}:bv_delta"),
        "citation_rate": citation_rate,
        "citation_rate_delta": _delta(f"{brand_name}:cr_delta"),
        "sentiment": sentiment,
        "sentiment_delta": _delta(f"{brand_name}:sent_delta"),
    }


def get_bv_trend(brand_name, metric_name, n_points=25, base_value=70):
    """Generate a deterministic daily trend series ending today for the Brand Visibility tab."""
    dates = []
    values = []
    today = datetime.now()
    for i in range(n_points):
        day = today - timedelta(days=(n_points - 1 - i))
        dates.append(day.strftime("%b %d"))
        seed = _bv_seed(f"{brand_name}:{metric_name}:{i}") % 100
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
    
    # Highlight the selected brand row
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

# Authentication handled by require_login() at top of file
# --- Sidebar Inputs ---
with st.sidebar:
    st.markdown("## 🌍 BrandSight GEO")
    st.caption("Generative Engine Optimization")
    
    st.write(f"Logged in as **{user.email}**")
    if st.button("Log out"):
        sign_out()
        st.rerun()
        
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
            from geo_audit_agent.agent import build_geo_audit_agent
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
            from multi_model import run_multi_model_audit
            multi_results = run_multi_model_audit(brand_name, category, city, use_real=False, user_id=st.session_state.get("user_id"))
            if "error" in multi_results:
                st.error(multi_results["error"])
                st.stop()
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
# Header
if st.session_state.audit_results:
    res = st.session_state.audit_results
    brand_name_val = res.get("brand_name", "Burger Hub")
    category_val = res.get("category", "fast food")
else:
    brand_name_val = "Burger Hub"
    category_val = "fast food"

# Page Header
st.markdown(f"""
<div style="margin-bottom: 24px;">
    <h1 style="font-size: 2.8rem; font-weight: 900; margin-bottom: 0;
        background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 50%, #EC4899 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        display: inline-block; letter-spacing: -0.04em;">
        📊 Brand Visibility Dashboard
    </h1>
    <p style="color: #64748B; font-size: 1.05rem; margin-top: 4px;">
        Full-spectrum AI search monitoring for <b style="color: #7C3AED;">{brand_name_val}</b> in <b>{category_val}</b>
    </p>
</div>
""", unsafe_allow_html=True)

# Determine metrics (for Burger Hub, keep exactly the requested values; for others, compute deterministically)
is_burger_hub = brand_name_val.lower() == "burger hub"

if is_burger_hub:
    bv_val = 60.0
    cr_val = 27.0
    sent_val = 72
    mentions_text = "1597 mentions out of 2663 total"
    citations_text = "719 citations in 2663 responses"
    sentiment_text = """
        <div style="display: flex; gap: 12px; justify-content: center; align-items: center; font-size: 0.85rem; font-weight: 700; margin-top: 6px;">
            <span style="color: #10B981; display: flex; align-items: center; gap: 4px;"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg> 1917</span>
            <span style="color: #64748B; display: flex; align-items: center; gap: 4px;"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line></svg> 682</span>
            <span style="color: #EF4444; display: flex; align-items: center; gap: 4px;"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm10-7h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"></path></svg> 64</span>
        </div>
    """
    platform_scores = [
        {"platform": "DeepSeek", "score": 99.5, "color": "linear-gradient(90deg, #0D9488, #14B8A6)"},
        {"platform": "Mistral", "score": 98.5, "color": "linear-gradient(90deg, #F59E0B, #FBBF24)"},
        {"platform": "Claude", "score": 91.2, "color": "linear-gradient(90deg, #EA580C, #F97316)"},
        {"platform": "Grok", "score": 77.2, "color": "linear-gradient(90deg, #DB2777, #EC4899)"},
        {"platform": "Gemini", "score": 74.8, "color": "linear-gradient(90deg, #7C3AED, #8B5CF6)"},
        {"platform": "ChatGPT", "score": 74.6, "color": "linear-gradient(90deg, #06B6D4, #22D3EE)"},
        {"platform": "Google AI Mo...", "score": 74.1, "color": "linear-gradient(90deg, #94A3B8, #CBD5E1)"},
        {"platform": "Google AI Ov...", "score": 64.6, "color": "linear-gradient(90deg, #64748B, #94A3B8)"},
        {"platform": "Perplexity", "score": 55.0, "color": "linear-gradient(90deg, #2563EB, #3B82F6)"},
        {"platform": "Copilot", "score": 47.5, "color": "linear-gradient(90deg, #3B82F6, #60A5FA)"},
    ]
else:
    # Deterministic dynamic values for other brands
    raw_scores = get_bv_platform_scores(brand_name_val)
    colors_list = [
        "linear-gradient(90deg, #0D9488, #14B8A6)",
        "linear-gradient(90deg, #F59E0B, #FBBF24)",
        "linear-gradient(90deg, #EA580C, #F97316)",
        "linear-gradient(90deg, #DB2777, #EC4899)",
        "linear-gradient(90deg, #7C3AED, #8B5CF6)",
        "linear-gradient(90deg, #06B6D4, #22D3EE)",
        "linear-gradient(90deg, #94A3B8, #CBD5E1)",
        "linear-gradient(90deg, #64748B, #94A3B8)",
        "linear-gradient(90deg, #2563EB, #3B82F6)",
        "linear-gradient(90deg, #3B82F6, #60A5FA)"
    ]
    platform_scores = []
    for idx, p in enumerate(raw_scores):
        name = p["platform"]
        if "Overview" in name:
            name = "Google AI Ov..."
        elif "Mode" in name:
            name = "Google AI Mo..."
        elif "Copilot" in name or "Bing" in name:
            name = "Copilot"
        platform_scores.append({
            "platform": name,
            "score": p["score"],
            "color": colors_list[idx % len(colors_list)]
        })
    bv_metrics = get_bv_metrics(brand_name_val, raw_scores)
    bv_val = bv_metrics["visibility"]
    cr_val = bv_metrics["citation_rate"]
    sent_val = bv_metrics["sentiment"]
    total_resp = 2663
    mentions_val = int(total_resp * (bv_val / 100))
    citations_val = int(total_resp * (cr_val / 100))
    mentions_text = f"{mentions_val} mentions out of {total_resp} total"
    citations_text = f"{citations_val} citations in {total_resp} responses"
    
    pos_count = int(total_resp * (sent_val / 100))
    neg_count = int((total_resp - pos_count) * 0.1)
    neu_count = total_resp - pos_count - neg_count
    
    sentiment_text = clean_html(f"""
        <div style="display: flex; gap: 12px; justify-content: center; align-items: center; font-size: 0.85rem; font-weight: 700; margin-top: 6px;">
            <span style="color: #10B981; display: flex; align-items: center; gap: 4px;"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg> {pos_count}</span>
            <span style="color: #64748B; display: flex; align-items: center; gap: 4px;"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line></svg> {neu_count}</span>
            <span style="color: #EF4444; display: flex; align-items: center; gap: 4px;"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm10-7h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"></path></svg> {neg_count}</span>
        </div>
    """)


# Custom SVG rendering helper function
def render_gauge_html(title, value_str, percent, sub_label, delta, delta_color, color, bottom_text):
    offset = 364.42 * (1 - percent / 100.0)
    raw_html = f"""
    <div style="background: #FFFFFF; border: 1px solid rgba(124, 58, 237, 0.08); border-radius: 20px; padding: 22px 24px; box-shadow: 0 8px 24px rgba(124, 58, 237, 0.06), 0 2px 8px rgba(0, 0, 0, 0.02); height: 100%;">
        <div style="font-family: 'Inter', sans-serif; font-size: 1rem; font-weight: 700; color: #0F172A; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            {title}
            <span style="color: #94A3B8; font-size: 0.85rem; cursor: pointer;" title="Details">🛈</span>
        </div>
        <div style="position: relative; display: flex; justify-content: center; align-items: center; height: 150px; margin: 12px 0;">
            <svg width="140" height="140" viewBox="0 0 140 140">
                <circle cx="70" cy="70" r="58" stroke="#F1F5F9" stroke-width="8" fill="transparent" />
                <circle cx="70" cy="70" r="58" stroke="{color}" stroke-width="8" fill="transparent"
                        stroke-dasharray="364.42" stroke-dashoffset="{offset}" stroke-linecap="round"
                        transform="rotate(-90 70 70)" />
            </svg>
            <div style="position: absolute; text-align: center;">
                <div style="font-family: 'Inter', sans-serif; font-size: 1.85rem; font-weight: 900; color: #0F172A; line-height: 1.1;">{value_str}</div>
                <div style="font-family: 'Inter', sans-serif; font-size: 0.72rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 3px;">{sub_label}</div>
                <div style="font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 700; color: {delta_color}; margin-top: 2px;">{delta}</div>
            </div>
        </div>
        <div style="font-family: 'Inter', sans-serif; font-size: 0.8rem; color: #64748B; text-align: center; border-top: 1px solid #F1F5F9; padding-top: 12px; margin-top: 4px;">
            {bottom_text}
        </div>
    </div>
    """
    return clean_html(raw_html)


# 4 Columns Row: 3 Gauges + Platform Breakdown
col_g1, col_g2, col_g3, col_pb = st.columns([1, 1, 1, 1.3])

with col_g1:
    st.markdown(render_gauge_html(
        title="Brand Visibility",
        value_str=f"{bv_val}%",
        percent=bv_val,
        sub_label="BV",
        delta="▲ +0.2%",
        delta_color="#10B981",
        color="#10B981",
        bottom_text=mentions_text
    ), unsafe_allow_html=True)

with col_g2:
    st.markdown(render_gauge_html(
        title="Citation Rate",
        value_str=f"{cr_val}%",
        percent=cr_val,
        sub_label="CR",
        delta="▲ +0.2%",
        delta_color="#10B981",
        color="#F59E0B",
        bottom_text=citations_text
    ), unsafe_allow_html=True)

with col_g3:
    st.markdown(render_gauge_html(
        title="Sentiment",
        value_str=f"{sent_val}%",
        percent=sent_val,
        sub_label="Positive",
        delta="▼ -0.4%" if is_burger_hub else "▲ +0.2%",
        delta_color="#EF4444" if is_burger_hub else "#10B981",
        color="#10B981",
        bottom_text=sentiment_text
    ), unsafe_allow_html=True)

with col_pb:
    # Platform breakdown progress bars
    rows_html = ""
    for idx, p in enumerate(platform_scores):
        rows_html += clean_html(f"""
        <div class="bv2-platform-item" style="padding: 6px 0;">
            <div class="bv2-platform-name" style="width: 120px; font-size: 0.85rem; font-weight: 600; color: #1E293B;">{p['platform']}</div>
            <div class="bv2-progress-bar-track" style="flex: 1; height: 8px; background: #F1F5F9; border-radius: 4px; overflow: hidden; margin: 0 10px;">
                <div class="bv2-progress-bar-fill" style="width: {p['score']}%; height: 100%; background: {p['color']}; border-radius: 4px;"></div>
            </div>
            <div class="bv2-platform-score" style="width: 45px; text-align: right; font-weight: 700; font-size: 0.85rem; color: #1E293B;">{p['score']}%</div>
        </div>
        """)
    st.markdown(clean_html(f"""
    <div style="background: #FFFFFF; border: 1px solid rgba(124, 58, 237, 0.08); border-radius: 20px; padding: 22px 24px; box-shadow: 0 8px 24px rgba(124, 58, 237, 0.06), 0 2px 8px rgba(0, 0, 0, 0.02); height: 100%;">
        <div style="font-family: 'Inter', sans-serif; font-size: 1rem; font-weight: 700; color: #0F172A; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
            <span>Brand Visibility By Platform</span>
            <div style="display: flex; gap: 8px;">
                <span style="color: #94A3B8; font-size: 0.85rem; cursor: pointer;">🛈</span>
                <span style="color: #94A3B8; font-size: 0.85rem; cursor: pointer;">↓</span>
            </div>
        </div>
        <div style="margin-top: 8px;">
            {rows_html}
        </div>
        <div style="font-family: 'Inter', sans-serif; font-size: 0.8rem; color: #64748B; text-align: center; border-top: 1px solid #F1F5F9; padding-top: 12px; margin-top: 12px;">
            10 platforms tracked &bull; 2,663 total responses
        </div>
    </div>
    """), unsafe_allow_html=True)


# Trend charts row side-by-side
st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
trend_col1, trend_col2 = st.columns(2)

bv_dates, bv_values = get_bv_trend(brand_name_val, "visibility", base_value=int(bv_val))
cr_dates, cr_values = get_bv_trend(brand_name_val, "citation_rate", base_value=int(cr_val) + 20)
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
    
    comp_data = get_competitor_data(brand_name_val, category_val)
    fig_multi = create_multi_model_chart(comp_data, brand_name_val, is_dark=(st.session_state.theme == "Dark"))
    st.plotly_chart(fig_multi, use_container_width=True, config={'displayModeBar': False})

    from geo_audit_agent.auth.user import render_tier_upgrade_prompt
    render_tier_upgrade_prompt(st.session_state.get("user_id"))

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

# Live Ticker activity feed at the bottom
st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
# st_autorefresh(interval=5000, key="bv_ticker_refresh")

ticker_mentions = int(bv_val * 26.63) + (_bv_seed(f"{brand_name_val}:{datetime.now().strftime('%Y%m%d%H%M%S')[:13]}") % 7)
ticker_citations = int(cr_val * 26.63) + (_bv_seed(f"{brand_name_val}:c:{datetime.now().strftime('%Y%m%d%H%M%S')[:13]}") % 5)

st.markdown(f"""
    <div style="background: rgba(124, 58, 237, 0.05); border: 1px solid rgba(124, 58, 237, 0.1); border-radius: 999px; padding: 12px 24px; text-align: center; font-weight: 600; color: #4C1D95; font-size: 0.9rem; font-family: 'Inter', sans-serif; display: flex; align-items: center; justify-content: center; gap: 8px; box-shadow: 0 4px 12px rgba(124, 58, 237, 0.03);">
        <span style="display: inline-block; width: 8px; height: 8px; background-color: #10B981; border-radius: 50%; animation: pulse 1.5s infinite; margin-right: 4px;"></span>
        🔄 Live activity: <b style="color: #7C3AED;">{ticker_mentions}</b> mentions &bull; <b style="color: #3B82F6;">{ticker_citations}</b> citations &bull; Last update: {datetime.now().strftime('%I:%M:%S %p')}
    </div>
    <style>
        @keyframes pulse {{
            0% {{ transform: scale(0.95); opacity: 0.5; }}
            50% {{ transform: scale(1.1); opacity: 1; }}
            100% {{ transform: scale(0.95); opacity: 0.5; }}
        }}
    </style>
""", unsafe_allow_html=True)

# Footer
st.sidebar.divider()
st.sidebar.markdown("""
    <div style='font-size: 0.75rem; color: #718096;'>
        <b>BrandSight GEO v1.2</b><br>
        Engine: LangGraph Orchestrator<br>
        &copy; 2026 Alchemist PANDA
    </div>
""", unsafe_allow_html=True)
