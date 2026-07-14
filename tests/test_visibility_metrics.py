from geo_audit_agent.metrics.visibility_metrics import Metric, calculate_visibility_metrics


def test_empty_metric_is_insufficient_not_zero():
    assert Metric(0, 0).value is None


def test_fixture_and_failed_rows_are_excluded():
    rows = [
        {"mode": "fixture", "mentioned": True, "provider": "openai", "prompt_id": "p"},
        {"mode": "failed", "mentioned": False, "provider": "google", "prompt_id": "p", "error": "timeout"},
    ]
    metrics = calculate_visibility_metrics(rows, expected_providers=["openai", "google"], expected_prompts=["p"])
    assert metrics.mention_rate.value is None
    assert metrics.provider_coverage.value == 0


def test_metrics_expose_numerator_denominator_and_sample_size():
    rows = [
        {"mode": "live", "mentioned": True, "recommended": True, "position": 2,
         "citation_urls": ["https://example.com"], "provider": "openai", "prompt_id": "p"},
        {"mode": "cached", "mentioned": False, "recommended": False, "position": None,
         "citation_urls": [], "provider": "google", "prompt_id": "p"},
    ]
    metrics = calculate_visibility_metrics(rows, expected_providers=["openai", "google"], expected_prompts=["p"])
    assert metrics.mention_rate.as_dict() == {"value": 0.5, "numerator": 1, "denominator": 2, "sample_size": 2}
    assert metrics.citation_rate.value == 0.5
    assert metrics.provider_coverage.value == 1.0
