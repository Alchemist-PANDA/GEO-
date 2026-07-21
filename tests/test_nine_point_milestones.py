from geo_audit_agent.metrics.keyword_metrics import calculate_keyword_metrics, keyword_trend
from geo_audit_agent.metrics.repeatability import calculate_repeatability
from geo_audit_agent.services.recommendation_evidence import attach_evidence


def test_keyword_metrics_use_only_successful_live_or_cached_rows():
    rows = [
        {"keyword": "best dentist Lahore", "mode": "live", "mentioned": True},
        {"keyword": "best dentist Lahore", "mode": "cached", "mentioned": False},
        {"keyword": "best dentist Lahore", "mode": "fixture", "mentioned": True},
    ]
    result = calculate_keyword_metrics(rows, "best dentist Lahore")
    assert result["numerator"] == 1
    assert result["denominator"] == 2


def test_keyword_trend_requires_two_real_periods():
    rows = [
        {"keyword": "accountant Pakistan", "run_date": "2026-07-19", "mode": "live", "mentioned": True},
        {"keyword": "accountant Pakistan", "run_date": "2026-07-20", "mode": "live", "mentioned": False},
    ]
    result = keyword_trend(rows, "accountant Pakistan")
    assert result["status"] == "measured"
    assert len(result["periods"]) == 2


def test_repeatability_does_not_turn_one_run_into_a_trend():
    assert calculate_repeatability([{"mode": "live", "mentioned": True}])["status"] == "insufficient_evidence"


def test_recommendations_are_cited_or_explicitly_marked_unverified():
    supported = attach_evidence([{"title": "Add LocalBusiness schema"}], {"evidence_urls": ["https://example.com/"]})
    unsupported = attach_evidence([{"title": "Improve authority"}], {})
    assert supported[0]["evidence_status"] == "supported"
    assert unsupported[0]["evidence_status"] == "unverified"
    assert "verify" in unsupported[0]["caveat"]
