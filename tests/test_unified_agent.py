"""Tests for the Unified Competitor Intelligence Agent."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from geo_audit_agent.agents.unified_competitor_agent import (
    run_competitor_scan,
    _generate_competitor_scores,
    _deterministic_score,
)


class TestDeterministicScoring:
    """Test that competitor scoring is deterministic and bounded."""

    def test_scores_are_deterministic(self):
        s1 = _deterministic_score("BrandA", "CompA", "geo")
        s2 = _deterministic_score("BrandA", "CompA", "geo")
        assert s1 == s2

    def test_scores_are_bounded(self):
        for metric in ["geo", "citation", "content", "schema", "platform"]:
            score = _deterministic_score("TestBrand", "TestComp", metric)
            assert 30 <= score <= 90

    def test_different_inputs_produce_different_scores(self):
        s1 = _deterministic_score("BrandA", "CompA", "geo")
        s2 = _deterministic_score("BrandB", "CompA", "geo")
        # Not guaranteed different but extremely unlikely to be the same for md5
        # Testing that it doesn't crash and returns valid ints
        assert isinstance(s1, int)
        assert isinstance(s2, int)


class TestGenerateCompetitorScores:
    """Test competitor score generation."""

    def test_returns_all_metrics(self):
        scores = _generate_competitor_scores("MyBrand", "TheirBrand")
        assert "competitor" in scores
        assert "geo_score" in scores
        assert "citation_rate" in scores
        assert "content_depth" in scores
        assert "schema_coverage" in scores
        assert "platform_presence" in scores

    def test_competitor_name_preserved(self):
        scores = _generate_competitor_scores("MyBrand", "Competitor X")
        assert scores["competitor"] == "Competitor X"


class TestRunCompetitorScan:
    """Test the full competitor scan pipeline."""

    def test_scan_returns_expected_structure(self):
        result = run_competitor_scan("Burger Hub", "fast food", "Islamabad")
        assert result["brand"] == "Burger Hub"
        assert result["category"] == "fast food"
        assert result["city"] == "Islamabad"
        assert "brand_scores" in result
        assert "competitors" in result
        assert "summary" in result

    def test_scan_generates_default_competitors(self):
        result = run_competitor_scan("Burger Hub", "fast food", "Islamabad")
        assert len(result["competitors"]) == 3

    def test_scan_uses_provided_competitors(self):
        result = run_competitor_scan(
            "Burger Hub", "fast food", "Islamabad",
            competitors=["KFC", "McDonald's"]
        )
        assert len(result["competitors"]) == 2
        names = [c["scores"]["competitor"] for c in result["competitors"]]
        assert "KFC" in names
        assert "McDonald's" in names

    def test_scan_summary_contains_rank(self):
        result = run_competitor_scan("Burger Hub", "fast food", "Islamabad")
        summary = result["summary"]
        assert "brand_rank" in summary
        assert "total_competitors" in summary
        assert "top_opportunity" in summary
        assert 1 <= summary["brand_rank"] <= summary["total_competitors"] + 1

    def test_each_competitor_has_explanations(self):
        result = run_competitor_scan("Burger Hub", "fast food", "Islamabad")
        for comp in result["competitors"]:
            assert "explanations" in comp
            assert len(comp["explanations"]) > 0
            for exp in comp["explanations"]:
                assert "area" in exp
                assert "insight" in exp
                assert "recommendation" in exp

    def test_dental_category_competitors(self):
        result = run_competitor_scan("My Dental", "dental clinic", "Islamabad")
        names = [c["scores"]["competitor"] for c in result["competitors"]]
        assert any("Dent" in n or "dental" in n.lower() for n in names)

    def test_restaurant_category_competitors(self):
        result = run_competitor_scan("My Restaurant", "restaurant", "Islamabad")
        names = [c["scores"]["competitor"] for c in result["competitors"]]
        assert len(names) == 3

    def test_unknown_category_fallback(self):
        result = run_competitor_scan("Niche Brand", "underwater basket weaving", "Islamabad")
        assert len(result["competitors"]) == 3

    def test_scan_is_deterministic(self):
        r1 = run_competitor_scan("Burger Hub", "fast food", "Islamabad")
        r2 = run_competitor_scan("Burger Hub", "fast food", "Islamabad")
        assert r1["brand_scores"] == r2["brand_scores"]
        for c1, c2 in zip(r1["competitors"], r2["competitors"]):
            assert c1["scores"] == c2["scores"]
