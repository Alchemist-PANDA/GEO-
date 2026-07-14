from geo_audit_agent.agents.unified_competitor_agent import run_competitor_scan


def _observation(entity: str, mentioned: bool, provider: str = "openai") -> dict:
    return {
        "entity": entity,
        "provider": provider,
        "prompt_id": "recommendation",
        "mode": "live",
        "mentioned": mentioned,
        "recommended": mentioned,
        "position": 1 if mentioned else None,
        "citation_urls": [],
    }


def test_scan_never_invents_competitors_or_scores():
    result = run_competitor_scan("Burger Hub", "fast food", "Islamabad")
    assert result["competitors"] == []
    assert result["summary"]["status"] == "insufficient_evidence"
    assert result["summary"]["brand_rank"] is None


def test_scan_requires_evidence_for_every_requested_entity():
    result = run_competitor_scan(
        "Burger Hub", "fast food", "Islamabad", competitors=["KFC"],
        observations=[_observation("Burger Hub", True)],
    )
    assert result["summary"]["status"] == "insufficient_evidence"
    assert result["competitors"][0]["sample_size"] == 0


def test_scan_computes_transparent_metrics_from_like_for_like_evidence():
    observations = [
        _observation("Burger Hub", True),
        _observation("Burger Hub", False, "google"),
        _observation("KFC", True),
        _observation("KFC", True, "google"),
    ]
    result = run_competitor_scan(
        "Burger Hub", "fast food", "Islamabad", competitors=["KFC"], observations=observations,
    )
    assert result["summary"]["status"] == "measured"
    mention = result["brand_scores"]["mention_rate"]
    assert mention == {"value": 0.5, "numerator": 1, "denominator": 2, "sample_size": 2}
    assert result["competitors"][0]["metrics"]["mention_rate"]["value"] == 1.0
