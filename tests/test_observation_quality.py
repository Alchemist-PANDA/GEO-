from geo_audit_agent.billing.plans import plan_allows_audit, plan_limits
from geo_audit_agent.metrics.observation import interpret_observation
from geo_audit_agent.metrics.visibility_metrics import Metric, wilson_interval


def test_mention_is_not_automatically_recommendation():
    result = interpret_observation("Acme is located downtown. Source: https://acme.example", "Acme")
    assert result.mentioned is True
    assert result.recommended is False
    assert result.sentiment == "neutral"
    assert result.citation_urls == ["https://acme.example"]


def test_ranked_positive_observation_is_recommendation():
    result = interpret_observation("1. Acme - highly recommended. https://acme.example", "Acme")
    assert result.recommended is True
    assert result.position == 1
    assert result.sentiment == "positive"
    assert result.confidence == 1.0


def test_negative_observation_is_not_recommendation():
    result = interpret_observation("Avoid Acme; customers report poor service.", "Acme")
    assert result.mentioned is True
    assert result.recommended is False
    assert result.sentiment == "negative"


def test_wilson_interval_is_absent_without_evidence():
    assert wilson_interval(0, 0) is None
    assert Metric(0, 0).value is None


def test_sme_entitlements_are_centralized():
    assert plan_allows_audit("starter", "express") is True
    assert plan_allows_audit("starter", "deep") is False
    assert plan_limits("professional")["white_label"] is True
