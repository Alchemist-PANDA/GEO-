"""Tests for the gap_analyst node logic."""
import os
import json
import tempfile
import pytest
from geo_audit_agent.agent import gap_analyst


class TestGapAnalyst:
    """Test suite for gap identification logic."""

    def _make_state(self, brand_name="Burger Hub"):
        return {
            "brand_name": brand_name,
            "category": "generic",
            "city": "Islamabad",
            "llm_response": "Some response",
            "is_cited": True,
            "confidence_score": 0.5,
            "gaps": [],
            "planned_actions": [],
            "remediation_results": [],
            "error": None,
        }

    def test_known_brand_produces_gaps(self):
        """Burger Hub has hardcoded data: no JSON-LD, no high authority."""
        state = self._make_state("Burger Hub")
        result = gap_analyst(state)
        gaps = result["gaps"]
        assert len(gaps) >= 1
        gap_types = [g["gap_type"] for g in gaps]
        assert "Structured Data" in gap_types

    def test_unknown_brand_gets_all_gaps(self):
        """Unknown brands should get all default gaps."""
        state = self._make_state("Totally Unknown Brand XYZ")
        result = gap_analyst(state)
        gaps = result["gaps"]
        gap_types = [g["gap_type"] for g in gaps]
        assert "Structured Data" in gap_types
        assert "Third-party Reviews" in gap_types
        assert "Authority Signals" in gap_types

    def test_severity_is_title_case(self):
        """All severity values should be title-case to match dashboard expectations."""
        state = self._make_state("Burger Hub")
        result = gap_analyst(state)
        for gap in result["gaps"]:
            sev = gap["severity"]
            assert sev == sev.title(), f"Severity '{sev}' is not title-case"
            assert sev in ("Critical", "High", "Medium", "Low"), f"Unexpected severity: {sev}"

    def test_config_file_overrides_defaults(self):
        """If a gap checklist JSON file exists, it should be used."""
        config = {
            "Test Brand": {
                "has_json_ld": True,
                "recent_reviews": True,
                "high_authority": True,
                "recency_mention": True,
                "geo_relevance": True
            }
        }
        # Create temp config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            os.environ["GAP_CHECKLIST_PATH"] = config_path
            state = self._make_state("Test Brand")
            result = gap_analyst(state)
            # All signals are True → no gaps
            assert len(result["gaps"]) == 0
        finally:
            os.environ.pop("GAP_CHECKLIST_PATH", None)
            os.unlink(config_path)

    def test_each_gap_has_required_fields(self):
        """Every gap must have gap_type, description, severity, tool_required."""
        state = self._make_state("Unknown Brand")
        result = gap_analyst(state)
        for gap in result["gaps"]:
            assert "gap_type" in gap
            assert "description" in gap
            assert "severity" in gap
            assert "tool_required" in gap
