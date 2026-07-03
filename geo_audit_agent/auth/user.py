import streamlit as st
from enum import Enum
from typing import List, Dict, Optional
from geo_audit_agent.db.session import get_session
from geo_audit_agent.db.models import UserProfile, AuditUsage
from sqlmodel import select
from datetime import date

class UserTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"

TIER_CONFIG: Dict[str, Dict] = {
    "free": {
        "models": [],  # All mock
        "audits_per_month": 3,
        "competitors": 3,
        "inspector": False,
        "action_agent": False,
        "self_improvement": False,
        "price": 0,
    },
    "starter": {
        "models": ["ChatGPT", "Gemini"],
        "audits_per_month": 50,
        "competitors": 5,
        "inspector": False,
        "action_agent": False,
        "self_improvement": False,
        "price": 29,
    },
    "professional": {
        "models": ["ChatGPT", "Gemini", "Claude.ai"],
        "audits_per_month": 150,
        "competitors": 10,
        "inspector": True,
        "action_agent": True,
        "self_improvement": False,
        "price": 49,
    },
    "business": {
        "models": ["ChatGPT", "Gemini", "Claude.ai", "Perplexity", "DeepSeek"],
        "audits_per_month": 500,
        "competitors": 20,
        "inspector": True,
        "action_agent": True,
        "self_improvement": True,
        "price": 99,
    },
    "enterprise": {
        "models": ["ChatGPT", "Gemini", "Claude.ai", "Perplexity", "DeepSeek", "Meta.ai", "Grok"],
        "audits_per_month": 999999,
        "competitors": 999999,
        "inspector": True,
        "action_agent": True,
        "self_improvement": True,
        "price": 249,
    },
}

def get_user_tier(user_id: str) -> str:
    """Get user's tier from database."""
    if not user_id:
        return "free"
    try:
        with get_session() as s:
            user = s.get(UserProfile, user_id)
            return user.tier if user else "free"
    except Exception:
        return "free"

def get_available_models(user_id: str) -> List[str]:
    """Get list of models available to the user."""
    tier = get_user_tier(user_id)
    return TIER_CONFIG.get(tier, {}).get("models", [])

def is_model_real(user_id: str, model_name: str) -> bool:
    """Check if a model should use real API or mock."""
    return model_name in get_available_models(user_id)

def get_audits_remaining(user_id: str) -> int:
    """Get remaining audits for the current month."""
    tier = get_user_tier(user_id)
    limit = TIER_CONFIG.get(tier, {}).get("audits_per_month", 3)
    try:
        with get_session() as s:
            today = date.today()
            current_month_start = today.replace(day=1)
            usages = s.exec(
                select(AuditUsage).where(
                    AuditUsage.user_id == user_id,
                    AuditUsage.audit_date >= current_month_start
                )
            ).all()
            used = sum(u.count for u in usages)
            return max(0, limit - used)
    except Exception:
        return limit

def can_run_audit(user_id: str) -> bool:
    """Check if user can run another audit this month."""
    return get_audits_remaining(user_id) > 0

def increment_audit_usage(user_id: str):
    """Increment audit count for the user."""
    try:
        with get_session() as s:
            today = date.today()
            usage = s.exec(
                select(AuditUsage).where(
                    AuditUsage.user_id == user_id,
                    AuditUsage.audit_date == today
                )
            ).first()
            if usage:
                usage.count += 1
                s.add(usage)
            else:
                s.add(AuditUsage(user_id=user_id, audit_date=today, count=1))
            s.commit()
    except Exception:
        pass

def update_user_tier(user_id: str, new_tier: str):
    """Update user's tier in database."""
    try:
        with get_session() as s:
            user = s.get(UserProfile, user_id)
            if user:
                user.tier = new_tier
                s.add(user)
                s.commit()
    except Exception:
        pass


def render_tier_upgrade_prompt(user_id: str):
    """Render upgrade prompt if user is on low tier."""
    tier = get_user_tier(user_id)
    if tier in ["free", "starter"]:
        st.info("🔒 **Upgrade to unlock more AI models and features!**")
        if st.button("Upgrade Now", key="upgrade_btn"):
            st.switch_page("pages/7_⚡_Billing.py")
