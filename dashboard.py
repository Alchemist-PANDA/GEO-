import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from run_lift_simulation import run_lift_simulation, simulate_improved_audit
from report_generator import generate_markdown_report

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Functions ---
def format_signed(value, decimals=2, suffix=""):
    """Format a number with proper sign (+, -, or nothing for zero)."""
    if value > 0:
        return f"+{value:.{decimals}f}{suffix}"
    elif value < 0:
        return f"{value:.{decimals}f}{suffix}"
    else:
        return f"0.{'0' * decimals}{suffix}"

def format_signed_percent(value):
    """Format a percentage with proper sign."""
    if value > 0:
        return f"+{value:.0f}%"
    elif value < 0:
        return f"{value:.0f}%"
    else:
        return "0%"

def clean_display_text(value):
    """Strip leaked HTML tags from text fields."""
    if not value:
        return ""
    value = str(value)
    for tag in ["</div>", "<div>", "<p>", "</p>", "<strong>", "</strong>", "<h4>", "</h4>"]:
        value = value.replace(tag, "")
    return value.strip()

DEFAULT_SIMULATION_DISCLAIMER = "This is a simulated improvement based on known ranking factors. Actual AI responses are highly dynamic and may vary depending on model updates, query phrasing, and regional data availability."

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Search Intelligence Platform",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Premium Design ---
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%);
    }

    /* Hero Section */
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 18px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.2);
    }

    .hero-title {
        font-size: 2.8rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.5rem;
        text-align: center;
    }

    .hero-subtitle {
        font-size: 1.2rem;
        color: rgba(255, 255, 255, 0.9);
        text-align: center;
        margin-bottom: 1rem;
        line-height: 1.6;
    }

    .hero-cta {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.8);
        text-align: center;
        font-weight: 500;
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 18px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }

    /* Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 18px;
        padding: 1.5rem;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.3);
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .metric-label {
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.7);
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Coverage Score Badge */
    .coverage-badge {
        display: inline-block;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        font-size: 1.1rem;
        font-weight: 600;
        margin: 1rem 0;
    }

    .badge-dominant { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; }
    .badge-strong { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
    .badge-emerging { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }
    .badge-weak { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; }
    .badge-invisible { background: linear-gradient(135deg, #4b4b4b 0%, #2b2b2b 100%); color: white; }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.03);
        padding: 0.5rem;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.6);
        font-weight: 500;
        padding: 0.75rem 1.5rem;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(15, 20, 25, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Text Colors */
    h1, h2, h3, h4, h5, h6 {
        color: white !important;
    }

    p, label, .stMarkdown {
        color: rgba(255, 255, 255, 0.85) !important;
    }

    /* Input Fields */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 8px;
        color: white;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        color: white !important;
    }

    /* Progress Bar */
    .stProgress > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* Info/Warning/Success Boxes */
    .stAlert {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        color: white;
    }

    /* Section Headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: white;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(102, 126, 234, 0.3);
    }

    /* Evidence Badge */
    .evidence-item {
        background: rgba(255, 255, 255, 0.04);
        border-left: 3px solid #667eea;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.85);
    }

    /* Priority Badges */
    .priority-high {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 0.5rem;
    }

    .priority-medium {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 0.5rem;
    }

    .priority-low {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Hero Section ---
st.markdown("""
<div class="hero-section">
    <div class="hero-title">AI Search Intelligence Platform</div>
    <div class="hero-subtitle">
        Measure, compare, and improve how your brand appears across ChatGPT, Claude, Gemini, and Perplexity.
    </div>
    <div class="hero-cta">
        Run an audit. Compare competitors. Prove visibility lift.
    </div>
</div>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "audit_results" not in st.session_state:
    st.session_state.audit_results = None
if "remediations" not in st.session_state:
    st.session_state.remediations = []
if "multi_model_results" not in st.session_state:
    st.session_state.multi_model_results = None
if "comparison_results" not in st.session_state:
    st.session_state.comparison_results = None
if "lift_results" not in st.session_state:
    st.session_state.lift_results = None
if "audit_history" not in st.session_state:
    st.session_state.audit_history = []

# --- Sidebar Configuration ---
with st.sidebar:
    st.markdown("### 🎯 Audit Configuration")
    with st.form("audit_form"):
        brand_name = st.text_input("Brand Name", value="Burger Hub")
        category = st.text_input("Category", value="fast food")
        city = st.text_input("City", value="Islamabad")

        st.markdown("**Known business facts / listing data**")
        business_context_text = st.text_area(
            "Business Context",
            value="",
            placeholder="4.5 rating, 231 Google reviews, swimming pool, sauna, spa, physiotherapy, Instagram 18.3K followers, Facebook 12.2K followers, F-9 Park Islamabad",
            help="Paste Google listing details, rating, review count, services, address, social links, or notes. This helps avoid false gaps.",
            height=100,
            label_visibility="collapsed"
        )

        run_audit = st.form_submit_button("🚀 Run GEO Audit", use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔧 Mode Selection")
    use_live_api = st.checkbox(
        "Enable Live API Mode",
        value=False,
        help="Use live provider APIs when keys are configured. Otherwise the app uses Simulated Demo Mode."
    )

    # Mode badge
    if use_live_api:
        api_key_present = bool(os.getenv("GROQ_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        if api_key_present:
            st.success("✅ Live API Mode")
        else:
            st.warning("⚠️ Live API Mode (no API key - will use Simulated Demo Mode)")
    else:
        st.info("🎭 Simulated Demo Mode")

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔍 Brand Audit",
    "🤖 AI Systems",
    "⚔️ Compare Brands",
    "📈 Lift Proof",
    "📚 History",
    "📄 Reports"
])

# --- TAB 1: Brand Audit ---
with tab1:
    if run_audit:
        with st.spinner(f"Running GEO Audit for {brand_name}..."):
            try:
                # Parse business context
                business_context = {}
                if business_context_text.strip():
                    # Simple parsing of business context
                    text = business_context_text.lower()

                    # Extract rating
                    import re
                    rating_match = re.search(r'(?:rated\s+|rating[:\s]+|)(\d+\.?\d*)\s*(?:google\s*)?rating', text)
                    if not rating_match:
                        rating_match = re.search(r'rated\s*(\d+\.?\d*)', text)
                    if not rating_match:
                        rating_match = re.search(r'rating[:\s]+(\d+\.?\d*)', text)

                    if rating_match:
                        business_context['rating'] = float(rating_match.group(1))

                    # Extract review count
                    review_match = re.search(r'(\d+)\s*(?:google\s*)?reviews?', text)
                    if review_match:
                        business_context['review_count'] = int(review_match.group(1))

                    # Extract services
                    services = []
                    service_keywords = ['swimming pool', 'pool', 'sauna', 'spa', 'physiotherapy', 'gym', 'steam', 'protein bar', 'online classes']
                    for keyword in service_keywords:
                        if keyword in text:
                            services.append(keyword)
                    if services:
                        business_context['services'] = services

                    # Extract social followers
                    instagram_match = re.search(r'instagram.*?\s*(\d+\.?\d*)\s*k', text)
                    if instagram_match:
                        business_context['instagram_followers'] = int(float(instagram_match.group(1)) * 1000)

                    facebook_match = re.search(r'facebook.*?\s*(\d+\.?\d*)\s*k', text)
                    if facebook_match:
                        business_context['facebook_followers'] = int(float(facebook_match.group(1)) * 1000)

                    # Extract location
                    if 'f-9' in text or 'park' in text or 'megazone' in text:
                        business_context['is_central_location'] = True

                        # Extract only location part (around park/megazone)
                        loc_match = re.search(r'([^,.]+?(?:f-9|park|megazone)[^,.]*)', text)
                        if loc_match:
                            business_context['location_description'] = loc_match.group(1).strip().title()
                        else:
                            business_context['location_description'] = "F-9 Park / Megazone, Islamabad"

                    # --- E-commerce specific extraction ---
                    # Extract platform
                    if 'shopify' in text:
                        business_context['platform'] = 'Shopify'
                        business_context['has_product_catalog'] = True  # Shopify stores typically have catalogs

                    # Extract return/exchange policy
                    if 'return' in text or 'exchange' in text or '14 day' in text or '14-day' in text:
                        business_context['has_return_policy'] = True
                        policy_match = re.search(r'(\d+)\s*[- ]?\s*day\s*(?:return|exchange)', text)
                        if policy_match:
                            business_context['return_policy_description'] = f"{policy_match.group(1)}-day exchange window"

                    # Extract payment options
                    payment_keywords = ['visa', 'mastercard', 'american express', 'amex', 'cod', 'cash on delivery']
                    found_payments = [kw for kw in payment_keywords if kw in text]
                    if found_payments:
                        business_context['has_payment_options'] = True
                        business_context['payment_options_description'] = ', '.join([p.title() for p in found_payments])

                    # Extract Instagram/social presence
                    if '@memeretail' in text or 'instagram' in text:
                        business_context['has_social_presence'] = True
                        # Try to extract follower count if present
                        instagram_ctx = re.search(r'(@\w+).*?(\d+\.?\d*)\s*k?\s*followers?', business_context_text, re.IGNORECASE)
                        if instagram_ctx:
                            business_context['instagram_followers'] = int(float(instagram_ctx.group(2)) * 1000)

                    # Extract market
                    market_match = re.search(r'market[:\s]+(\w+)', text)
                    if market_match:
                        business_context['market'] = market_match.group(1).title()

                    # Store original category for e-commerce detection
                    business_context['category'] = category

                    # Mark schema as not present by default (will be checked by template)
                    # Let the template decide based on business_context

                    # --- E-commerce specific extraction ---
                    # Extract platform
                    if 'shopify' in text:
                        business_context['platform'] = 'Shopify'
                        business_context['has_product_catalog'] = True  # Shopify stores typically have catalogs

                    # Extract return/exchange policy
                    if 'return' in text or 'exchange' in text or '14 day' in text or '14-day' in text:
                        business_context['has_return_policy'] = True
                        policy_match = re.search(r'(\d+)\s*[- ]?\s*day\s*(?:return|exchange)', text)
                        if policy_match:
                            business_context['return_policy_description'] = f"{policy_match.group(1)}-day exchange window"

                    # Extract payment options
                    payment_keywords = ['visa', 'mastercard', 'american express', 'amex', 'cod', 'cash on delivery']
                    found_payments = [kw for kw in payment_keywords if kw in text]
                    if found_payments:
                        business_context['has_payment_options'] = True
                        business_context['payment_options_description'] = ', '.join([p.title() for p in found_payments])

                    # Extract Instagram/social presence
                    if '@memeretail' in text or 'instagram' in text:
                        business_context['has_social_presence'] = True
                        # Try to extract follower count if present
                        instagram_ctx = re.search(r'(@\w+).*?(\d+\.?\d*)\s*k?\s*followers?', business_context_text, re.IGNORECASE)
                        if instagram_ctx:
                            business_context['instagram_followers'] = int(float(instagram_ctx.group(2)) * 1000)

                    # Extract market
                    market_match = re.search(r'market[:\s]+(\w+)', text)
                    if market_match:
                        business_context['market'] = market_match.group(1).title()

                    # Store original category for e-commerce detection
                    business_context['category'] = category

                    # Preserve raw text for industry-specific strength detection
                    business_context["raw_text"] = business_context_text
                    business_context["business_context_text"] = business_context_text

                    # Mark schema as not present by default (will be checked by template)
                    # Let the template decide based on business_context

                # Send both brand and brand_name for backward compatibility
                inputs = {
                    "brand": brand_name,
                    "brand_name": brand_name,
                    "category": category,
                    "city": city,
                    "business_context": business_context,
                    "raw_business_context": business_context_text,
                    "force_mock": not use_live_api,
                    "use_real": use_live_api
                }

                # Debug mode - show payload if DEBUG_MODE env var is set
                if os.getenv("DEBUG_MODE", "").lower() == "true":
                    st.write("DEBUG payload keys:", list(inputs.keys()))
                    st.write("DEBUG payload:", inputs)

                st.info("BRAND_AUDIT_CALL_PATH: dashboard.py -> run_lift_simulation direct bypass")
                results = run_lift_simulation(
                    brand_name,
                    category,
                    city,
                    inputs
                )
                st.session_state.audit_results = results

                # Initialize remediations state safely
                st.session_state.remediations = []
                remediation_data = results.get("remediation", [])
                for res in remediation_data:
                    if isinstance(res, str):
                        st.session_state.remediations.append({
                            "tool": "Remediation Recommendation",
                            "content": res,
                            "status": "Pending"
                        })
                    elif isinstance(res, dict):
                        st.session_state.remediations.append({
                            "tool": res.get("tool", "Unknown Tool"),
                            "content": res.get("output_preview", "No preview available"),
                            "status": "Pending"
                        })

                # Display call path and template info immediately
                st.caption(f"Call path: {results.get('call_path', 'MISSING')}")
                st.caption(f"Template used: {results.get('template_used', 'MISSING')}")

                st.success("✅ Audit Completed!")
            except Exception as e:
                st.error(f"❌ Audit failed: {e}")
                logger.error(f"Audit error: {e}")

    # --- Display Results ---
    if st.session_state.audit_results:
        res = st.session_state.audit_results

        st.markdown('<div class="section-header">📊 Audit Results</div>', unsafe_allow_html=True)

        # Metric Cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            is_cited = res.get("citation_found", False)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{"✅" if is_cited else "❌"}</div>
                <div class="metric-label">Citation Status</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            confidence = res.get("confidence_score", 0.0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{confidence:.2f}</div>
                <div class="metric-label">Confidence Score</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(float(confidence))

        with col3:
            sentiment = res.get("sentiment", "none")
            sentiment_emoji = {"positive": "🟢", "neutral": "🟡", "negative": "🔴", "none": "⚪"}
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{sentiment_emoji.get(sentiment, "⚪")}</div>
                <div class="metric-label">Sentiment: {sentiment.title()}</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            gaps_count = len(res.get("gaps", []))
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{gaps_count}</div>
                <div class="metric-label">Gaps Identified</div>
            </div>
            """, unsafe_allow_html=True)

        # Template used display
        template_used = res.get("template_used", "Generic")
        if template_used != "Generic":
            st.success(f"📋 Using **{template_used}** for industry-specific recommendations")
        else:
            st.warning(f"⚠️ Using Generic template - no industry match for category: {res.get('category', 'unknown')}")

        st.caption(f"Call path: {res.get('call_path', 'MISSING')}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Details Expanders
        with st.expander("📝 AI Response Analysis"):
            st.markdown("**Raw AI Response:**")
            st.code(res.get("raw_response", "No response content."), language=None)

        with st.expander("💪 Strengths Identified"):
            strengths = res.get("strengths", [])
            if strengths:
                for strength in strengths:
                    st.success(f"**{strength.get('title', 'Strength')}**: {strength.get('description', '')}")
            else:
                st.info("No strengths identified yet.")

        with st.expander("🔍 Competitors Identified"):
            competitors = res.get("competitors", [])
            if competitors:
                for comp in competitors:
                    st.markdown(f"• {comp}")
            else:
                st.info("No competitors identified.")

        with st.expander("🚩 Identified Gaps"):
            gaps = res.get("gaps", [])
            if gaps:
                for gap in gaps:
                    if isinstance(gap, str):
                        st.warning(gap)
                    elif isinstance(gap, dict):
                        gap_title = gap.get('title', gap.get('gap_type', 'Gap'))
                        gap_severity = gap.get('severity', 'unknown')
                        gap_desc = gap.get('description', '')
                        st.warning(f"**{gap_title}** ({gap_severity}): {gap_desc}")
            else:
                st.success("✅ No critical gaps identified!")

        # --- Remediation Panel ---
        st.markdown('<div class="section-header">🛠️ Remediation & Content Review</div>', unsafe_allow_html=True)
        st.info("Review, edit, and approve the AI-generated remediation content below.")

        # Prefer new remediation format over old remediation_results
        remediation_list = res.get("remediation", [])

        # Warning if gaps exist but no remediation
        gaps = res.get("gaps", [])
        if gaps and not remediation_list:
            st.warning("⚠️ Gaps were found, but no remediation was generated. This indicates a remediation pipeline issue.")

        if remediation_list:
            # Deduplicate by title
            seen_titles = set()
            unique_remediation = []
            for item in remediation_list:
                if isinstance(item, dict):
                    title = item.get('title', '')
                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        unique_remediation.append(item)
                    elif not title:
                        unique_remediation.append(item)

            for idx, item in enumerate(unique_remediation):
                if isinstance(item, dict) and 'title' in item:
                    with st.container():
                        # Extract fields
                        title = item.get('title', 'Remediation')
                        priority = item.get('priority', 'medium').upper()
                        rec_type = item.get('type', 'general')
                        reason = item.get('reason', '')
                        why = item.get('why_this_works', '')
                        action = item.get('action', '')
                        effort = item.get('effort', 'medium').title()
                        impact = item.get('impact', 'medium').title()
                        quick_win = item.get('quick_win', False)

                        # Render using Streamlit components
                        st.markdown(f"### 🔧 {title}")

                        # Priority and quick win badges
                        badge_text = f"**Priority:** {priority}"
                        if quick_win:
                            badge_text += " ⚡ **Quick Win**"
                        st.markdown(badge_text)

                        st.markdown(f"**Type:** {rec_type}")

                        if reason:
                            st.markdown(f"**Why this matters:** {reason}")

                        if why:
                            st.markdown(f"**Why this works:** {why}")

                        st.markdown(f"**Effort:** {effort} | **Impact:** {impact}")

                        # Action plan text area
                        edited_content = st.text_area(
                            "Action plan",
                            value=action,
                            height=120,
                            key=f"edit_{idx}",
                            help="Edit the action plan before approving"
                        )

                        # Approve/Reject buttons
                        c1, c2, c3 = st.columns([1, 1, 2])
                        with c1:
                            if st.button("✅ Approve", key=f"app_{idx}"):
                                st.toast(f"✅ Approved: {title}")
                        with c2:
                            if st.button("❌ Reject", key=f"rej_{idx}"):
                                st.toast(f"❌ Rejected: {title}")

                        st.markdown("---")

            # --- Export Section ---
            st.markdown("<br>", unsafe_allow_html=True)
            export_data = {
                "brand": res.get("brand_name", res.get("brand", "Unknown")),
                "category": res.get("category", ""),
                "city": res.get("city", ""),
                "status": "completed",
                "gaps": gaps,
                "remediation": unique_remediation
            }
            json_export = json.dumps(export_data, indent=4)
            st.download_button(
                label="📥 Export Client-Ready Report",
                data=json_export,
                file_name=f"geo_remediation_{res.get('brand_name', res.get('brand', 'unknown')).lower().replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.write("No remediation results to display.")

# --- TAB 2: AI Systems ---
with tab2:
    st.markdown('<div class="section-header">🤖 Multi-Model AI Visibility Testing</div>', unsafe_allow_html=True)
    st.markdown("Test your brand's visibility across ChatGPT, Claude, Gemini, and Perplexity.")

    with st.form("multi_model_form"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            mm_brand = st.text_input("Brand Name", value="Burger Hub", key="mm_brand")
        with col_b:
            mm_category = st.text_input("Category", value="fast food", key="mm_category")
        with col_c:
            mm_city = st.text_input("City", value="Islamabad", key="mm_city")

        run_multi_audit = st.form_submit_button("🚀 Run Multi-Model Audit", use_container_width=True)

    if run_multi_audit:
        with st.spinner(f"Testing {mm_brand} across 4 AI systems..."):
            try:
                results = run_multi_model_audit(mm_brand, mm_category, mm_city, use_real=use_live_api)
                st.session_state.multi_model_results = results
                st.success("✅ Multi-model audit completed!")
            except Exception as e:
                st.error(f"❌ Multi-model audit failed: {e}")
                logger.error(f"Multi-model audit error: {e}")

    if st.session_state.multi_model_results:
        mm_res = st.session_state.multi_model_results
        summary = mm_res["summary"]

        # Data source disclaimer
        data_source = summary.get("data_source", "simulated")
        if data_source == "simulated":
            st.warning("⚠️ **Simulated Demo Mode**: These results use deterministic sample outputs for demonstration purposes. They do not represent live AI model responses. Enable Live API Mode in the sidebar to test with real APIs.")
        elif data_source == "mixed":
            st.info("ℹ️ **Mixed Mode**: Some results are from live APIs, others are simulated due to missing API keys.")
        else:
            st.success("✅ **Live API Mode**: Results are based on actual API responses.")

        # GEO Coverage Score - Hero Display
        st.markdown('<div class="section-header">🎯 GEO Coverage Score</div>', unsafe_allow_html=True)

        coverage_score = summary["geo_coverage_score"]
        coverage_label = summary["coverage_label"]

        badge_class = f"badge-{coverage_label.lower()}"

        col_score, col_info = st.columns([1, 2])

        with col_score:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{coverage_score}%</div>
                <div class="metric-label">Coverage Score</div>
                <div class="coverage-badge {badge_class}">{coverage_label}</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(coverage_score / 100)

        with col_info:
            st.markdown(f"""
            <div class="glass-card">
                <p style="font-size: 0.9rem; color: rgba(255,255,255,0.7); margin-bottom: 0.5rem;">
                    <strong>Based on:</strong> ChatGPT, Claude, Gemini, Perplexity
                </p>
                <p style="font-size: 1rem; color: rgba(255,255,255,0.9);">
                    {summary['coverage_explanation']}
                </p>
            </div>
            """, unsafe_allow_html=True)

        # Evidence Breakdown
        with st.expander("📋 Coverage Breakdown (Evidence Trace)"):
            for model_result in mm_res["results"]:
                status_icon = "✅" if model_result["mentioned"] else "❌"
                st.markdown(f"""
                <div class="evidence-item">
                    {status_icon} <strong>{model_result['model']}</strong> → {model_result['evidence']}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Key Insight
        st.info(f"**🔥 Key Insight:** {summary['insight']}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Summary Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{summary["models_tested"]}</div>
                <div class="metric-label">AI Systems Tested</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{summary["models_mentioned"]}</div>
                <div class="metric-label">Systems with Visibility</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            visibility_pct = int(summary["visibility_score"] * 100)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{visibility_pct}%</div>
                <div class="metric-label">Visibility Score</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-header">📊 Visibility by AI System</div>', unsafe_allow_html=True)

        # Results by Model
        for model_result in mm_res["results"]:
            # Determine display label based on mode
            mode = model_result.get('mode', 'simulated')
            model_name = model_result['model']
            provider = model_result.get('provider', '')

            # Only show Live API for Groq or specific live models
            if model_name == 'Perplexity':
                display_label = f"{model_name} — Simulated Demo"
            elif mode == 'live_api':
                display_label = f"{model_name} — Live API"
            else:
                display_label = f"{model_name} — Simulated Demo"

            status = "✅ Mentioned" if model_result["mentioned"] else "❌ Not Mentioned"
            with st.expander(f"**{display_label}** - {status}"):
                col_a, col_b, col_c, col_d = st.columns(4)

                with col_a:
                    st.write("**Mentioned:**")
                    st.write("✅ Yes" if model_result['mentioned'] else "❌ No")

                with col_b:
                    st.write("**Position:**")
                    if model_result['position']:
                        st.write(f"#{model_result['position']}")
                    else:
                        st.write("—")

                with col_c:
                    st.write("**Sentiment:**")
                    sentiment_emoji = {
                        "positive": "🟢",
                        "neutral": "🟡",
                        "negative": "🔴",
                        "none": "⚪"
                    }
                    st.write(f"{sentiment_emoji.get(model_result['sentiment'], '⚪')} {model_result['sentiment'].title()}")

                with col_d:
                    st.write("**Mode:**")
                    if model_name == 'Perplexity':
                        st.write("🎭 Simulated Demo")
                    else:
                        mode_label = "✅ Live API" if mode == 'live_api' else "🎭 Simulated Demo"
                        st.write(mode_label)

                st.write("**Raw AI Response:**")
                st.code(model_result['raw_response'], language=None)

        st.markdown("<br>", unsafe_allow_html=True)

        # Cross-Platform Analysis
        st.markdown('<div class="section-header">🌐 Cross-Platform Analysis</div>', unsafe_allow_html=True)
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("""
            <div class="glass-card">
                <h4>✅ Visible In</h4>
            </div>
            """, unsafe_allow_html=True)
            if summary['mentioned_models']:
                for model in summary['mentioned_models']:
                    st.markdown(f"• {model}")
            else:
                st.write("None")

        with col_right:
            st.markdown("""
            <div class="glass-card">
                <h4>❌ Missing From</h4>
            </div>
            """, unsafe_allow_html=True)
            if summary['not_mentioned_models']:
                for model in summary['not_mentioned_models']:
                    st.markdown(f"• {model}")
            else:
                st.write("None")

# --- TAB 3: Compare Brands ---
with tab3:
    st.markdown('<div class="section-header">⚔️ Brand Comparison</div>', unsafe_allow_html=True)
    st.markdown("Compare your brand's AI visibility against competitors.")

    with st.form("comparison_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Brand A**")
            brand_a = st.text_input("Brand A Name", value="Burger Hub", key="brand_a")
        with col_b:
            st.markdown("**Brand B**")
            brand_b = st.text_input("Brand B Name", value="Shake Shack", key="brand_b")

        col_cat, col_city = st.columns(2)
        with col_cat:
            comp_category = st.text_input("Category", value="fast food", key="comp_category")
        with col_city:
            comp_city = st.text_input("City", value="New York", key="comp_city")

        run_comparison = st.form_submit_button("⚔️ Run Comparison", use_container_width=True)

    if run_comparison:
        with st.spinner(f"Comparing {brand_a} vs {brand_b}..."):
            try:
                comparison = compare_brands(brand_a, brand_b, comp_category, comp_city, force_mock=True)
                st.session_state.comparison_results = comparison
                st.success("✅ Comparison completed!")
            except Exception as e:
                st.error(f"❌ Comparison failed: {e}")
                logger.error(f"Comparison error: {e}")

    if st.session_state.comparison_results:
        comp = st.session_state.comparison_results

        # Winner Display
        winner = comp.get("winner", "tie")
        winner_reason = comp.get("winner_reason", "")

        if winner == "tie":
            st.markdown(f"""
            <div class="glass-card" style="text-align: center; padding: 2rem;">
                <h2>🤝 Competitive Tie</h2>
                <p style="font-size: 1.1rem; color: rgba(255,255,255,0.8);">{winner_reason}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            winner_emoji = "🏆" if winner == brand_a else "🥇"
            st.markdown(f"""
            <div class="glass-card" style="text-align: center; padding: 2rem; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);">
                <h2>{winner_emoji} Winner: {winner}</h2>
                <p style="font-size: 1.1rem; color: rgba(255,255,255,0.8);">{winner_reason}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Side-by-side comparison
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown(f"""
            <div class="glass-card">
                <h3>{brand_a}</h3>
            </div>
            """, unsafe_allow_html=True)

            audit_a = comp.get("audit_a", {})
            score_a = audit_a.get("confidence_score", 0.0)
            cited_a = audit_a.get("citation_found", False)
            sentiment_a = audit_a.get("sentiment", "none")
            position_a = audit_a.get("citation_position_score", 0.0)

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{score_a:.2f}</div>
                <div class="metric-label">Confidence Score</div>
            </div>
            """, unsafe_allow_html=True)

            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.write(f"**Cited:** {'✅ Yes' if cited_a else '❌ No'}")
            with col_a2:
                sentiment_emoji = {"positive": "🟢", "neutral": "🟡", "negative": "🔴", "none": "⚪"}
                st.write(f"**Sentiment:** {sentiment_emoji.get(sentiment_a, '⚪')} {sentiment_a.title()}")

        with col_right:
            st.markdown(f"""
            <div class="glass-card">
                <h3>{brand_b}</h3>
            </div>
            """, unsafe_allow_html=True)

            audit_b = comp.get("audit_b", {})
            score_b = audit_b.get("confidence_score", 0.0)
            cited_b = audit_b.get("citation_found", False)
            sentiment_b = audit_b.get("sentiment", "none")
            position_b = audit_b.get("citation_position_score", 0.0)

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{score_b:.2f}</div>
                <div class="metric-label">Confidence Score</div>
            </div>
            """, unsafe_allow_html=True)

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.write(f"**Cited:** {'✅ Yes' if cited_b else '❌ No'}")
            with col_b2:
                sentiment_emoji = {"positive": "🟢", "neutral": "🟡", "negative": "🔴", "none": "⚪"}
                st.write(f"**Sentiment:** {sentiment_emoji.get(sentiment_b, '⚪')} {sentiment_b.title()}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Competitive Actions
        st.markdown('<div class="section-header">🎯 Recommended Actions</div>', unsafe_allow_html=True)
        actions = comp.get("actions", [])
        if actions:
            for action in actions:
                st.markdown(f"""
                <div class="glass-card">
                    <h4>{action}</h4>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No specific actions recommended at this time.")

# --- TAB 4: Lift Proof ---
with tab4:
    st.markdown('<div class="section-header">📈 Visibility Lift Proof</div>', unsafe_allow_html=True)
    st.markdown("Demonstrate measurable improvements in AI visibility.")

    with st.form("lift_form"):
        lift_brand = st.text_input("Brand Name", value="Burger Hub", key="lift_brand")
        lift_category = st.text_input("Category", value="fast food", key="lift_category")
        lift_city = st.text_input("City", value="Islamabad", key="lift_city")
        run_lift = st.form_submit_button("📈 Generate Lift Simulation", use_container_width=True)

    if run_lift:
        with st.spinner(f"Generating lift simulation for {lift_brand}..."):
            try:
                # Run baseline audit via direct path
                baseline = run_lift_simulation(
                    lift_brand,
                    lift_category,
                    lift_city,
                    {"force_mock": True}
                )

                # Simulate improvement
                improved = simulate_improved_audit(baseline)

                # Calculate lift to determine success message
                baseline_score = baseline.get("confidence_score", 0.0)
                improved_score = improved.get("confidence_score", 0.0)
                lift_amount = improved_score - baseline_score

                st.session_state.lift_results = {
                    "baseline": baseline,
                    "improved": improved,
                    "brand": lift_brand
                }

                # Show appropriate message based on lift
                if baseline_score >= 0.85 and abs(lift_amount) <= 0.05:
                    st.info("ℹ️ Already strong visibility — no meaningful lift detected.")
                elif baseline_score >= 0.85:
                    st.info("ℹ️ Already strong visibility — focus on maintenance and monitoring.")
                elif lift_amount < 0:
                    st.warning("⚠️ No lift detected — visibility decreased in this simulation.")
                else:
                    st.success("✅ Lift simulation completed!")
            except Exception as e:
                st.error(f"❌ Lift simulation failed: {e}")
                logger.error(f"Lift simulation error: {e}")

    if st.session_state.lift_results:
        lift = st.session_state.lift_results
        baseline = lift["baseline"]
        improved = lift["improved"]
        brand = lift["brand"]

        # Lift Metrics
        st.markdown('<div class="section-header">📊 Lift Metrics</div>', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        baseline_score = baseline.get("confidence_score", 0.0)
        improved_score = improved.get("confidence_score", 0.0)
        lift_amount = improved_score - baseline_score
        lift_pct = (lift_amount / baseline_score * 100) if baseline_score > 0 else 0

        # Determine lift status
        if baseline_score >= 0.85:
            lift_status = "already_strong"
            if abs(lift_amount) <= 0.05:
                lift_message = "No meaningful lift detected"
            else:
                lift_message = "Already strong visibility"
            lift_color = "#667eea"
        elif lift_amount < 0:
            lift_status = "negative"
            lift_message = "Visibility decreased"
            lift_color = "#f5576c"
        elif lift_amount > 0.1:
            lift_status = "significant"
            lift_message = "Significant improvement"
            lift_color = "#38ef7d"
        elif lift_amount > 0:
            lift_status = "moderate"
            lift_message = "Moderate improvement"
            lift_color = "#11998e"
        else:
            lift_status = "no_change"
            lift_message = "No significant change"
            lift_color = "#667eea"

        # Format signed numbers correctly
        lift_amount_str = format_signed(lift_amount)
        lift_pct_str = format_signed_percent(lift_pct)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{baseline_score:.2f}</div>
                <div class="metric-label">Before Score</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{improved_score:.2f}</div>
                <div class="metric-label">After Score</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 3px solid {lift_color};">
                <div class="metric-value" style="color: {lift_color};">{lift_amount_str}</div>
                <div class="metric-label">Absolute Lift</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 3px solid {lift_color};">
                <div class="metric-value" style="color: {lift_color};">{lift_pct_str}</div>
                <div class="metric-label">Percentage Lift</div>
            </div>
            """, unsafe_allow_html=True)

        # Lift status message
        if lift_status == "already_strong":
            st.info(f"ℹ️ **{lift_message}** (baseline {baseline_score:.2f}). This brand already appears strongly in the baseline response. Improvements should focus on maintaining accuracy, closing platform-specific gaps, and monitoring AI visibility over time.")
        elif lift_status == "negative":
            st.warning(f"⚠️ **{lift_message}**: This simulation shows a decline of {abs(lift_pct):.1f}%. The brand may already have strong baseline visibility, or the simulated improvements were not effective.")
        elif lift_status == "significant":
            st.success(f"✅ **{lift_message}**: Confidence increased by {lift_pct:.1f}%")
        elif lift_status == "moderate":
            st.success(f"✅ **{lift_message}**: Confidence increased by {lift_pct:.1f}%")
        else:
            st.info(f"ℹ️ **{lift_message}**")

        st.markdown("<br>", unsafe_allow_html=True)

        # Before/After Comparison
        st.markdown('<div class="section-header">🔄 Before vs After: AI Response Transformation</div>', unsafe_allow_html=True)

        col_before, col_after = st.columns(2)

        with col_before:
            st.markdown("""
            <div class="glass-card">
                <h4>🔴 BEFORE</h4>
            </div>
            """, unsafe_allow_html=True)
            before_response = baseline.get("raw_response", "")
            st.code(before_response, language=None)

            st.write(f"**Citation Found:** {'✅ Yes' if baseline.get('citation_found') else '❌ No'}")
            st.write(f"**Sentiment:** {baseline.get('sentiment', 'none').title()}")

        with col_after:
            st.markdown("""
            <div class="glass-card">
                <h4>🟢 AFTER</h4>
            </div>
            """, unsafe_allow_html=True)
            after_response = improved.get("raw_response", "")
            st.code(after_response, language=None)

            st.write(f"**Citation Found:** {'✅ Yes' if improved.get('citation_found') else '❌ No'}")
            st.write(f"**Sentiment:** {improved.get('sentiment', 'none').title()}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Simulation Credibility
        st.markdown('<div class="section-header">⚖️ Simulation Credibility</div>', unsafe_allow_html=True)

        confidence_level = improved.get("simulation_confidence", "medium")
        confidence_colors = {"high": "green", "medium": "orange", "low": "red"}
        confidence_color = confidence_colors.get(confidence_level, "gray")

        # Safe access to simulation_notes with defaults
        simulation_notes = improved.get("simulation_notes") or {}
        disclaimer = simulation_notes.get("disclaimer", DEFAULT_SIMULATION_DISCLAIMER)
        alternative_outcomes = simulation_notes.get("alternative_outcomes", [])
        risk_factors = simulation_notes.get("risk_factors", [])

        st.markdown(f"""
        <div class="glass-card">
            <p><strong>Simulation Confidence:</strong> <span style="color: {confidence_color}; font-weight: 600; text-transform: uppercase;">{confidence_level}</span></p>
            <p style="font-size: 0.9rem; color: rgba(255,255,255,0.7);">
                ⚠️ {disclaimer}
            </p>
        </div>
        """, unsafe_allow_html=True)

        if alternative_outcomes or risk_factors:
            col_alt, col_risk = st.columns(2)

            with col_alt:
                st.markdown("**Alternative Outcomes:**")
                if alternative_outcomes:
                    for outcome in alternative_outcomes:
                        st.markdown(f"• {outcome}")
                else:
                    st.info("No alternative outcomes provided")

            with col_risk:
                st.markdown("**Risk Factors:**")
                if risk_factors:
                    for risk in risk_factors:
                        st.markdown(f"• {risk}")
                else:
                    st.info("No risk factors provided")

# --- TAB 5: History ---
with tab5:
    st.markdown('<div class="section-header">📚 Audit History</div>', unsafe_allow_html=True)
    st.markdown("Track your brand's AI visibility over time.")

    # Add current audit to history when run
    if st.session_state.audit_results and st.session_state.audit_results not in st.session_state.audit_history:
        audit_with_timestamp = st.session_state.audit_results.copy()
        audit_with_timestamp["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.audit_history.append(audit_with_timestamp)

    if st.session_state.audit_history:
        st.markdown(f"**Total Audits:** {len(st.session_state.audit_history)}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Display history in reverse chronological order
        for idx, audit in enumerate(reversed(st.session_state.audit_history)):
            with st.expander(f"**{audit.get('brand', 'Unknown')}** - {audit.get('timestamp', 'N/A')}"):
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Confidence", f"{audit.get('confidence_score', 0.0):.2f}")
                with col2:
                    st.metric("Citation", "✅" if audit.get('citation_found') else "❌")
                with col3:
                    st.metric("Sentiment", audit.get('sentiment', 'none').title())
                with col4:
                    st.metric("Gaps", len(audit.get('gaps', [])))

                st.write(f"**Category:** {audit.get('category', 'N/A')}")
                st.write(f"**City:** {audit.get('city', 'N/A')}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Clear history button
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.audit_history = []
            st.rerun()

    else:
        st.info("No audit history yet. Run an audit in the Brand Audit tab to start tracking.")

# --- TAB 6: Reports ---
with tab6:
    st.markdown('<div class="section-header">📄 Export Reports</div>', unsafe_allow_html=True)
    st.markdown("Generate client-ready reports and documentation.")

    if st.session_state.audit_results:
        st.markdown("""
        <div class="glass-card">
            <h4>📊 Available Reports</h4>
            <p>Generate professional reports from your audit results.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Markdown Report
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📝 Markdown Report**")
            st.write("Comprehensive markdown report with all audit details.")

            if st.button("Generate Markdown Report", key="gen_md"):
                try:
                    markdown_report = generate_markdown_report(
                        st.session_state.audit_results,
                        lift_report=st.session_state.lift_results
                    )

                    brand = st.session_state.audit_results.get("brand", "unknown")
                    filename = f"geo_report_{brand.lower().replace(' ', '_')}.md"

                    st.download_button(
                        label="📥 Download Markdown Report",
                        data=markdown_report,
                        file_name=filename,
                        mime="text/markdown",
                        use_container_width=True
                    )
                    st.success("✅ Report generated!")
                except Exception as e:
                    st.error(f"❌ Report generation failed: {e}")

        with col2:
            st.markdown("**📊 JSON Export**")
            st.write("Raw audit data in JSON format for integrations.")

            audit_json = json.dumps(st.session_state.audit_results, indent=2)
            brand = st.session_state.audit_results.get("brand", "unknown")
            filename = f"geo_audit_{brand.lower().replace(' ', '_')}.json"

            st.download_button(
                label="📥 Download JSON Data",
                data=audit_json,
                file_name=filename,
                mime="application/json",
                use_container_width=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Multi-Model Report
        if st.session_state.multi_model_results:
            st.markdown("""
            <div class="glass-card">
                <h4>🤖 Multi-Model Report</h4>
            </div>
            """, unsafe_allow_html=True)

            mm_json = json.dumps(st.session_state.multi_model_results, indent=2)
            brand = st.session_state.multi_model_results["summary"].get("mentioned_models", ["unknown"])[0] if st.session_state.multi_model_results["summary"].get("mentioned_models") else "unknown"
            filename = f"geo_multimodel_{brand.lower().replace(' ', '_')}.json"

            st.download_button(
                label="📥 Download Multi-Model Report (JSON)",
                data=mm_json,
                file_name=filename,
                mime="application/json",
                use_container_width=True
            )

        # Comparison Report
        if st.session_state.comparison_results:
            st.markdown("""
            <div class="glass-card">
                <h4>⚔️ Comparison Report</h4>
            </div>
            """, unsafe_allow_html=True)

            comp_json = json.dumps(st.session_state.comparison_results, indent=2)
            filename = "geo_comparison_report.json"

            st.download_button(
                label="📥 Download Comparison Report (JSON)",
                data=comp_json,
                file_name=filename,
                mime="application/json",
                use_container_width=True
            )

    else:
        st.info("No audit results available. Run an audit in the Brand Audit tab to generate reports.")

# Footer
st.sidebar.divider()
st.sidebar.caption("AI Search Intelligence Platform v2.0")
