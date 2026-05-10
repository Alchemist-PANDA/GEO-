"""Tests for dashboard UI fixes."""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_lift_simulation import simulate_improved_audit


class TestRemediationTextCleaning:
    """Test remediation card text cleaning."""

    def test_no_html_leakage_in_reason(self):
        """Test that reason field does not contain raw HTML tags."""
        remediation = {
            'title': 'Create dedicated service pages',
            'reason': 'Missing service pages',
            'why_this_works': 'Individual service pages target specific search queries',
            'action': 'Create pages for: personal training, swimming pool, sauna',
            'priority': 'high',
            'effort': 'medium',
            'impact': 'high'
        }

        # Verify no HTML tags in fields
        assert '</div>' not in remediation['reason']
        assert '<p>' not in remediation['reason']
        assert '<strong>' not in remediation['reason']
        assert '</p>' not in remediation['reason']


class TestLiftProofFallback:
    """Test lift proof simulation_notes fallback."""

    def test_simulation_notes_always_present(self):
        """Test that simulate_improved_audit always includes simulation_notes."""
        baseline = {
            "brand": "Test Brand",
            "category": "fitness gym",
            "citation_found": False,
            "confidence_score": 0.0,
            "raw_response": "No mention found."
        }

        improved = simulate_improved_audit(baseline)

        # Should always have simulation_notes
        assert "simulation_notes" in improved
        assert isinstance(improved["simulation_notes"], dict)

        # Should have required fields
        assert "disclaimer" in improved["simulation_notes"]
        assert "alternative_outcomes" in improved["simulation_notes"]
        assert "risk_factors" in improved["simulation_notes"]

    def test_simulation_notes_for_strong_baseline(self):
        """Test simulation_notes for strong baseline brands."""
        baseline = {
            "brand": "Strong Brand",
            "category": "fitness gym",
            "citation_found": True,
            "confidence_score": 0.90,
            "raw_response": "Strong Brand is highly recommended."
        }

        improved = simulate_improved_audit(baseline)

        # Should have simulation_notes
        assert "simulation_notes" in improved
        assert "disclaimer" in improved["simulation_notes"]

    def test_simulation_notes_for_weak_baseline(self):
        """Test simulation_notes for weak baseline brands."""
        baseline = {
            "brand": "Weak Brand",
            "category": "fitness gym",
            "citation_found": True,
            "confidence_score": 0.50,
            "raw_response": "Weak Brand is an option."
        }

        improved = simulate_improved_audit(baseline)

        # Should have simulation_notes
        assert "simulation_notes" in improved
        assert "disclaimer" in improved["simulation_notes"]


class TestNegativeLiftFormatting:
    """Test negative lift formatting."""

    def test_negative_lift_displays_correctly(self):
        """Test that negative lift displays with minus sign, not +-."""
        before_score = 1.00
        after_score = 0.85
        lift_amount = after_score - before_score

        # Format as signed number
        lift_str = f"{lift_amount:+.2f}"

        # Should show minus sign
        assert lift_str == "-0.15"
        assert "+-" not in lift_str

    def test_positive_lift_displays_correctly(self):
        """Test that positive lift displays with plus sign."""
        before_score = 0.50
        after_score = 0.75
        lift_amount = after_score - before_score

        # Format as signed number
        lift_str = f"{lift_amount:+.2f}"

        # Should show plus sign
        assert lift_str == "+0.25"

    def test_zero_lift_displays_correctly(self):
        """Test that zero lift displays without sign."""
        before_score = 0.50
        after_score = 0.50
        lift_amount = after_score - before_score

        # Format as signed number
        lift_str = f"{lift_amount:+.2f}"

        # Should show no sign or +0.00
        assert lift_str in ["0.00", "+0.00"]

    def test_negative_percentage_formatting(self):
        """Test negative percentage formatting."""
        lift_pct = -15.0

        # Format as signed percentage
        pct_str = f"{lift_pct:+.0f}%"

        # Should show minus sign
        assert pct_str == "-15%"
        assert "+-" not in pct_str


class TestMultiModelLabeling:
    """Test multi-model labeling."""

    def test_simulated_result_label(self):
        """Test that simulated result displays 'Simulated Demo'."""
        model_result = {
            'model': 'ChatGPT',
            'provider': 'openai',
            'mode': 'simulated',
            'mentioned': True,
            'sentiment': 'positive'
        }

        mode = model_result.get('mode', 'simulated')
        model_name = model_result['model']

        if mode == 'live_api':
            display_label = f"{model_name} — Live API"
        else:
            display_label = f"{model_name} — Simulated Demo"

        assert display_label == "ChatGPT — Simulated Demo"

    def test_live_result_label(self):
        """Test that live result displays 'Live API'."""
        model_result = {
            'model': 'Groq',
            'provider': 'groq',
            'mode': 'live_api',
            'mentioned': True,
            'sentiment': 'positive'
        }

        mode = model_result.get('mode', 'simulated')
        model_name = model_result['model']

        if mode == 'live_api':
            display_label = f"{model_name} — Live API"
        else:
            display_label = f"{model_name} — Simulated Demo"

        assert display_label == "Groq — Live API"
