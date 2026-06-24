"""Tests for the check_citation node logic."""
import pytest
from geo_audit_agent.agent import check_citation


class TestCheckCitation:
    """Test suite for brand citation detection and confidence scoring."""

    def _make_state(self, brand_name, llm_response):
        return {
            "brand_name": brand_name,
            "category": "fast food",
            "city": "Islamabad",
            "llm_response": llm_response,
            "is_cited": None,
            "confidence_score": None,
            "gaps": [],
            "planned_actions": [],
            "remediation_results": [],
            "error": None,
        }

    def test_exact_match_full_confidence(self):
        state = self._make_state("Burger Hub", "The best place is Burger Hub in Islamabad.")
        result = check_citation(state)
        assert result["is_cited"] is True
        assert result["confidence_score"] == 1.0

    def test_no_match_zero_confidence(self):
        state = self._make_state("Burger Hub", "Try Cheezious or Howdy for great food.")
        result = check_citation(state)
        assert result["is_cited"] is False
        assert result["confidence_score"] == 0.0

    def test_partial_match_graduated_score(self):
        """When some brand words match, score should be proportional."""
        state = self._make_state("Burger Hub", "This hub has the best burgers around.")
        result = check_citation(state)
        # "burger" and "hub" are both >2 chars and both appear
        assert result["confidence_score"] == 1.0
        assert result["is_cited"] is True

    def test_partial_match_one_word(self):
        """Only one of two brand words matches."""
        state = self._make_state("Burger Hub", "This place has great pizza and a fun hub area.")
        result = check_citation(state)
        # "hub" matches but "burger" doesn't → 0.5
        assert result["confidence_score"] == 0.5
        assert result["is_cited"] is True

    def test_error_response_zero_confidence(self):
        state = self._make_state("Burger Hub", "Error: API call failed. Connection timeout")
        result = check_citation(state)
        assert result["is_cited"] is False
        assert result["confidence_score"] == 0.0

    def test_none_response_zero_confidence(self):
        state = self._make_state("Burger Hub", None)
        result = check_citation(state)
        assert result["is_cited"] is False
        assert result["confidence_score"] == 0.0

    def test_empty_response_zero_confidence(self):
        state = self._make_state("Burger Hub", "")
        result = check_citation(state)
        assert result["is_cited"] is False
        assert result["confidence_score"] == 0.0

    def test_case_insensitive_match(self):
        state = self._make_state("Burger Hub", "BURGER HUB is amazing!")
        result = check_citation(state)
        assert result["is_cited"] is True
        assert result["confidence_score"] == 1.0

    def test_short_brand_words_ignored(self):
        """Words with <=2 chars should not contribute to scoring."""
        state = self._make_state("Al Baik", "The chicken at this place is great.")
        result = check_citation(state)
        # "al" is <=2 chars, only "baik" counts; "baik" not in response → 0.0
        assert result["confidence_score"] == 0.0
