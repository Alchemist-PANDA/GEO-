import pytest

from geo_audit_agent.api.routes.audits import audit_tier_allowed


@pytest.mark.parametrize("plan,tier,allowed", [
    ("free", "express", False),
    ("starter", "express", True),
    ("starter", "balanced", False),
    ("professional", "balanced", True),
    ("professional", "deep", False),
    ("business", "deep", True),
    ("enterprise", "deep", True),
    ("unknown", "express", False),
])
def test_live_audit_entitlements(plan, tier, allowed):
    assert audit_tier_allowed(plan, tier) is allowed
