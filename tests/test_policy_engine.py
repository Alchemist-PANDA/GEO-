from geo_audit_agent.policy.engine import PolicyEngine

def test_blocks_deploy_without_audit():
    res = PolicyEngine().enforce({"intent": "deploy", "audit_status": "pending",
                                  "human_approved": True, "brand_known": True})
    assert res["allowed"] is False
    assert any(b["id"] == "POL-001" for b in res["blocking"])

def test_recommendation_requires_evidence():
    res = PolicyEngine().enforce({"intent": "recommend", "evidence": []})
    assert res["allowed"] is False
    assert any(b["id"] == "POL-002" for b in res["blocking"])

def test_comparisons_require_competitor_data():
    res = PolicyEngine().enforce({"intent": "compare", "competitor_data": None})
    assert res["allowed"] is False
    assert any(b["id"] == "POL-003" for b in res["blocking"])

def test_confidence_score_warning():
    res = PolicyEngine().enforce({"intent": "recommend", "evidence": ["Some evidence"], "confidence": None})
    assert res["allowed"] is True  # Warning does not block
    assert any(w["id"] == "POL-004" for w in res["warnings"])

def test_invented_score_blocked():
    res = PolicyEngine().enforce({"score_present": True, "score_source": None})
    assert res["allowed"] is False
    assert any(b["id"] == "POL-005" for b in res["blocking"])

def test_brand_must_exist():
    res = PolicyEngine().enforce({"intent": "audit", "brand_known": False})
    assert res["allowed"] is False
    assert any(b["id"] == "POL-006" for b in res["blocking"])

def test_deployment_requires_human_approval():
    res = PolicyEngine().enforce({"intent": "deploy", "audit_status": "complete", "human_approved": False, "brand_known": True})
    assert res["allowed"] is False
    assert any(b["id"] == "POL-007" for b in res["blocking"])

def test_evaluation_before_deployment():
    res = PolicyEngine().enforce({"intent": "deploy", "audit_status": "complete", "human_approved": True, "brand_known": True, "inspector_passed": False})
    assert res["allowed"] is False
    assert any(b["id"] == "POL-008" for b in res["blocking"])

def test_allows_clean_deploy():
    res = PolicyEngine().enforce({"intent": "deploy", "audit_status": "complete",
        "human_approved": True, "brand_known": True, "inspector_passed": True})
    assert res["allowed"] is True
