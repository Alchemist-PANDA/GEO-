import os
os.environ["FORCE_MOCK"] = "true"

from geo_audit_agent.policy.engine import PolicyEngine


def test_blocks_deploy_without_audit():
    res = PolicyEngine().enforce({"intent": "deploy", "audit_status": "pending",
                                  "human_approved": True, "brand_known": True})
    assert res["allowed"] is False
    assert any(b["id"] == "POL-001" for b in res["blocking"])


def test_allows_clean_deploy():
    res = PolicyEngine().enforce({"intent": "deploy", "audit_status": "complete",
        "human_approved": True, "brand_known": True, "inspector_passed": True})
    assert res["allowed"] is True


def test_blocks_recommend_without_evidence():
    res = PolicyEngine().enforce({"intent": "recommend", "evidence": None})
    assert res["allowed"] is False
    assert any(b["id"] == "POL-002" for b in res["blocking"])


def test_warns_recommend_without_confidence():
    res = PolicyEngine().enforce({"intent": "recommend", "evidence": ["some data"],
                                  "confidence": None})
    assert res["allowed"] is True
    assert any(w["id"] == "POL-004" for w in res["warnings"])


def test_blocks_deploy_without_human_approval():
    res = PolicyEngine().enforce({"intent": "deploy", "audit_status": "complete",
                                  "human_approved": False, "brand_known": True})
    assert res["allowed"] is False
    assert any(b["id"] == "POL-007" for b in res["blocking"])


def test_blocks_compare_without_data():
    res = PolicyEngine().enforce({"intent": "compare", "competitor_data": None})
    assert res["allowed"] is False
    assert any(b["id"] == "POL-003" for b in res["blocking"])


def test_blocks_unknown_brand():
    res = PolicyEngine().enforce({"intent": "audit", "brand_known": False})
    assert res["allowed"] is False
    assert any(b["id"] == "POL-006" for b in res["blocking"])


def test_blocks_failed_inspector():
    res = PolicyEngine().enforce({"intent": "deploy", "audit_status": "complete",
        "human_approved": True, "brand_known": True, "inspector_passed": False})
    assert res["allowed"] is False
    assert any(b["id"] == "POL-008" for b in res["blocking"])
