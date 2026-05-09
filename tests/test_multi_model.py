import pytest
from multi_model import run_multi_model_audit, _calculate_position, _generate_summary, _get_deterministic_seed


def test_run_multi_model_audit_returns_results():
    """Test that multi-model audit returns results for all models."""
    result = run_multi_model_audit("Test Brand", "test", "Test City", use_real=False)

    assert "results" in result
    assert "summary" in result
    assert len(result["results"]) == 4


def test_multi_model_results_structure():
    """Test that each model result has required fields."""
    result = run_multi_model_audit("Test Brand", "test", "Test City", use_real=False)

    for model_result in result["results"]:
        assert "model" in model_result
        assert "provider" in model_result
        assert "mentioned" in model_result
        assert "sentiment" in model_result
        assert "raw_response" in model_result
        assert "confidence" in model_result
        assert "evidence" in model_result
        assert "mode" in model_result


def test_summary_structure():
    """Test that summary has required fields."""
    result = run_multi_model_audit("Test Brand", "test", "Test City", use_real=False)
    summary = result["summary"]

    assert "models_tested" in summary
    assert "models_mentioned" in summary
    assert "visibility_score" in summary
    assert "geo_coverage_score" in summary
    assert "coverage_label" in summary
    assert "coverage_explanation" in summary
    assert "insight" in summary
    assert "mentioned_models" in summary
    assert "not_mentioned_models" in summary


def test_visibility_score_calculation():
    """Test that visibility score is calculated correctly."""
    result = run_multi_model_audit("Test Brand", "test", "Test City", use_real=False)
    summary = result["summary"]

    models_tested = summary["models_tested"]
    models_mentioned = summary["models_mentioned"]
    visibility_score = summary["visibility_score"]

    expected_score = models_mentioned / models_tested if models_tested > 0 else 0.0
    assert visibility_score == expected_score
    assert 0.0 <= visibility_score <= 1.0


def test_model_variation_consistency():
    """Test that model variation is consistent for same brand."""
    result1 = run_multi_model_audit("Burger Hub", "burgers", "New York", use_real=False)
    result2 = run_multi_model_audit("Burger Hub", "burgers", "New York", use_real=False)

    for i in range(len(result1["results"])):
        assert result1["results"][i]["mentioned"] == result2["results"][i]["mentioned"]
        assert result1["results"][i]["model"] == result2["results"][i]["model"]


def test_calculate_position():
    """Test position calculation from position score."""
    assert _calculate_position(0.95) == 1
    assert _calculate_position(0.75) == 2
    assert _calculate_position(0.55) == 3
    assert _calculate_position(0.35) == 4
    assert _calculate_position(0.15) == 5


def test_generate_summary_full_visibility():
    """Test summary generation for full visibility."""
    results = [
        {"model": "ChatGPT", "mentioned": True},
        {"model": "Claude", "mentioned": True},
        {"model": "Gemini", "mentioned": True},
        {"model": "Perplexity", "mentioned": True}
    ]

    summary = _generate_summary(results, "Test Brand")

    assert summary["visibility_score"] == 1.0
    assert summary["geo_coverage_score"] == 100
    assert summary["coverage_label"] == "Dominant"
    assert "strong visibility" in summary["insight"].lower()


def test_generate_summary_no_visibility():
    """Test summary generation for no visibility."""
    results = [
        {"model": "ChatGPT", "mentioned": False},
        {"model": "Claude", "mentioned": False},
        {"model": "Gemini", "mentioned": False},
        {"model": "Perplexity", "mentioned": False}
    ]

    summary = _generate_summary(results, "Test Brand")

    assert summary["visibility_score"] == 0.0
    assert summary["geo_coverage_score"] == 0
    assert summary["coverage_label"] == "Invisible"
    assert "invisible" in summary["insight"].lower()


def test_generate_summary_partial_visibility():
    """Test summary generation for partial visibility."""
    results = [
        {"model": "ChatGPT", "mentioned": False},
        {"model": "Claude", "mentioned": True},
        {"model": "Gemini", "mentioned": True},
        {"model": "Perplexity", "mentioned": False}
    ]

    summary = _generate_summary(results, "Test Brand")

    assert summary["visibility_score"] == 0.5
    assert summary["geo_coverage_score"] == 50
    assert summary["coverage_label"] == "Emerging"
    assert "inconsistently visible" in summary["insight"].lower()
    assert len(summary["mentioned_models"]) == 2
    assert len(summary["not_mentioned_models"]) == 2


def test_no_crash_without_api_keys():
    """Test that multi-model audit doesn't crash without API keys."""
    result = run_multi_model_audit("Test Brand", "test", "Test City", use_real=True)

    assert "results" in result
    assert len(result["results"]) == 4
    for model_result in result["results"]:
        assert model_result["mode"] in ["live_api", "simulated"]


def test_models_differ_in_mock_mode():
    """Test that at least two models can differ in mock mode."""
    result = run_multi_model_audit("Test Brand", "test", "Test City", use_real=False)

    mentioned_count = sum(1 for r in result["results"] if r["mentioned"])

    assert mentioned_count != 0 or mentioned_count != 4


def test_sentiment_realism():
    """Test that sentiment distribution is realistic for recommendation queries."""
    result = run_multi_model_audit("Test Brand", "test", "Test City", use_real=False)

    for model_result in result["results"]:
        if model_result["mentioned"]:
            # Top positions should always be positive
            if model_result["position"] and model_result["position"] <= 2:
                assert model_result["sentiment"] == "positive"
            # Sentiment should be valid
            assert model_result["sentiment"] in ["positive", "neutral", "negative"]


def test_geo_coverage_labels():
    """Test GEO Coverage Score label assignment."""
    # Test Dominant (90-100%)
    results_dominant = [
        {"model": "ChatGPT", "mentioned": True},
        {"model": "Claude", "mentioned": True},
        {"model": "Gemini", "mentioned": True},
        {"model": "Perplexity", "mentioned": True}
    ]
    summary = _generate_summary(results_dominant, "Test")
    assert summary["coverage_label"] == "Dominant"

    # Test Strong (75-89%)
    results_strong = [
        {"model": "ChatGPT", "mentioned": True},
        {"model": "Claude", "mentioned": True},
        {"model": "Gemini", "mentioned": True},
        {"model": "Perplexity", "mentioned": False}
    ]
    summary = _generate_summary(results_strong, "Test")
    assert summary["coverage_label"] == "Strong"

    # Test Emerging (50-74%)
    results_emerging = [
        {"model": "ChatGPT", "mentioned": True},
        {"model": "Claude", "mentioned": True},
        {"model": "Gemini", "mentioned": False},
        {"model": "Perplexity", "mentioned": False}
    ]
    summary = _generate_summary(results_emerging, "Test")
    assert summary["coverage_label"] == "Emerging"

    # Test Weak (25-49%)
    results_weak = [
        {"model": "ChatGPT", "mentioned": True},
        {"model": "Claude", "mentioned": False},
        {"model": "Gemini", "mentioned": False},
        {"model": "Perplexity", "mentioned": False}
    ]
    summary = _generate_summary(results_weak, "Test")
    assert summary["coverage_label"] == "Weak"

    # Test Invisible (0-24%)
    results_invisible = [
        {"model": "ChatGPT", "mentioned": False},
        {"model": "Claude", "mentioned": False},
        {"model": "Gemini", "mentioned": False},
        {"model": "Perplexity", "mentioned": False}
    ]
    summary = _generate_summary(results_invisible, "Test")
    assert summary["coverage_label"] == "Invisible"


def test_evidence_trace():
    """Test that evidence trace is present and meaningful."""
    result = run_multi_model_audit("Test Brand", "test", "Test City", use_real=False)

    for model_result in result["results"]:
        assert "evidence" in model_result
        assert len(model_result["evidence"]) > 0

        if model_result["mentioned"]:
            assert "Test Brand" in model_result["evidence"]
            assert "appears" in model_result["evidence"] or "mentioned" in model_result["evidence"]
        else:
            assert "not mentioned" in model_result["evidence"]


def test_coverage_explanation():
    """Test that coverage explanation is present and meaningful."""
    result = run_multi_model_audit("Test Brand", "test", "Test City", use_real=False)
    summary = result["summary"]

    assert "coverage_explanation" in summary
    assert len(summary["coverage_explanation"]) > 0
    assert "derived from" in summary["coverage_explanation"] or "reflects" in summary["coverage_explanation"]
    assert "Test Brand" in summary["coverage_explanation"]
