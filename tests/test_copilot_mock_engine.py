from geo_audit_agent.copilot import engine, mock_engine


def _base_context(**overrides):
    context = {
        "brand_name": "Burger Hub",
        "category": "fast food",
        "city": "Islamabad",
        "confidence_score": 0.72,
        "is_cited": True,
        "gaps": [
            {"gap_type": "Missing Schema", "severity": "Critical", "description": "No LocalBusiness schema found."},
            {"gap_type": "Thin Content", "severity": "Medium", "description": "Location pages lack detail."},
        ],
        "geo_coverage_score": 0.55,
        "model_results": [
            {"model": "ChatGPT", "mentioned": True, "confidence": 0.8},
            {"model": "Claude", "mentioned": False, "confidence": 0.2},
        ],
        "competitor_summary": {"brand_rank": 2, "total_competitors": 3, "top_opportunity": "Schema Coverage"},
        "competitors": [
            {
                "scores": {"competitor": "Rival Burgers", "geo_score": 80, "citation_rate": 70,
                           "content_depth": 75, "schema_coverage": 90, "platform_presence": 60},
                "explanations": [{"area": "Schema Coverage", "insight": "They use rich schema.", "recommendation": "Add LocalBusiness schema."}],
            }
        ],
        "brand_scores": {"geo_score": 60, "citation_rate": 55, "content_depth": 65, "schema_coverage": 30, "platform_presence": 70},
        "chart_title": None,
        "chart_data": None,
        "fig_json": None,
    }
    context.update(overrides)
    return context


def test_greeting_mentions_brand():
    response = mock_engine.generate_response("hello", _base_context())
    assert "Burger Hub" in response


def test_score_answer_uses_real_numbers():
    response = mock_engine.generate_response("how is my score doing?", _base_context())
    assert "72%" in response
    assert "55%" in response


def test_gap_answer_orders_by_severity():
    response = mock_engine.generate_response("what should i fix first?", _base_context())
    assert response.index("Missing Schema") < response.index("Thin Content")


def test_competitor_named_comparison():
    response = mock_engine.generate_response("show me Burger Hub vs Rival Burgers", _base_context())
    assert "unavailable" in response
    assert "No values have been estimated" in response


def test_competitor_overview_without_name():
    response = mock_engine.generate_response("how do I compare to competitors?", _base_context())
    assert "like-for-like live observations" in response


def test_explain_chart_uses_chart_title():
    context = _base_context(chart_title="Multi-Model Benchmark Chart", fig_json="{}")
    response = mock_engine.generate_response("Explain this chart: Multi-Model Benchmark Chart", context)
    assert "Multi-Model Benchmark Chart" in response


def test_fallback_for_vague_question():
    response = mock_engine.generate_response("asdkjhasd", _base_context())
    assert "Great question" in response or "Try asking" in response


def test_no_data_gracefully_handled():
    context = _base_context(gaps=[], competitors=[], model_results=[])
    response = mock_engine.generate_response("what should i fix first?", context)
    assert "Burger Hub" in response


def test_engine_falls_back_to_mock_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert engine.is_live_mode() is False
    response = engine.get_response("hello", _base_context())
    assert "Burger Hub" in response


def test_engine_does_not_substitute_demo_on_live_failure(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")

    def _boom(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(engine, "_live_response", _boom)
    response = engine.get_response("hello", _base_context())
    assert "temporarily unavailable" in response
    assert "No simulated answer" in response
