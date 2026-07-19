"""SME-first plans.

Limits are intentionally explicit and centralized so the UI cannot advertise a
different entitlement from the API.
"""

from __future__ import annotations

PLAN_CONFIG: dict[str, dict] = {
    "free": {
        "models": [], "audits_per_month": 3, "competitors": 3, "brands": 1,
        "inspector": False, "action_agent": False, "self_improvement": False,
        "white_label": False, "price": 0,
    },
    "starter": {
        "models": ["ChatGPT", "Gemini"], "audits_per_month": 50, "competitors": 5, "brands": 3,
        "inspector": False, "action_agent": False, "self_improvement": False,
        "white_label": False, "price": 29,
    },
    "professional": {
        "models": ["ChatGPT", "Gemini", "Claude.ai"], "audits_per_month": 150, "competitors": 10, "brands": 15,
        "inspector": True, "action_agent": True, "self_improvement": False,
        "white_label": True, "price": 49,
    },
    "business": {
        "models": ["ChatGPT", "Gemini", "Claude.ai", "Perplexity", "DeepSeek"],
        "audits_per_month": 500, "competitors": 20, "brands": 50, "inspector": True,
        "action_agent": True, "self_improvement": True, "white_label": True, "price": 99,
    },
    "enterprise": {
        "models": ["ChatGPT", "Gemini", "Claude.ai", "Perplexity", "DeepSeek", "Meta.ai", "Grok"],
        "audits_per_month": 999999, "competitors": 999999, "brands": 999999,
        "inspector": True, "action_agent": True, "self_improvement": True,
        "white_label": True, "price": 249,
    },
}

TIER_RANK = {"express": 0, "balanced": 1, "deep": 2}
MAX_AUDIT_TIER = {"free": None, "starter": "express", "professional": "balanced", "business": "deep", "enterprise": "deep"}


def plan_limits(plan: str) -> dict:
    return PLAN_CONFIG.get(plan, PLAN_CONFIG["free"])


def plan_allows_audit(plan: str, tier: str) -> bool:
    maximum = MAX_AUDIT_TIER.get(plan)
    return maximum is not None and tier in TIER_RANK and TIER_RANK[tier] <= TIER_RANK[maximum]
