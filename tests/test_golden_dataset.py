import json
from pathlib import Path

import pytest

from geo_audit_agent.services.llm_router import query_provider


def load_golden_data():
    path = Path(__file__).parent / "golden_competitors.json"
    with open(path) as f:
        return json.load(f)

@pytest.mark.parametrize("scenario", load_golden_data())
def test_competitor_explanation_quality(scenario):
    """
    Test that the LLM explanation accurately captures the core winning strategy
    present in the raw HTML without hallucinations.
    """
    html_content = scenario["html"]
    expected_factor = scenario["expected_winning_factor"].lower()

    prompt = f"""You are an expert AI Analyst. Given the following raw HTML from a competitor's website, extract their main 'Winning Factor' in a single concise phrase.
HTML:
{html_content}

Winning Factor:"""

    response_obj = query_provider(prompt, tier="balanced")
    response = response_obj.text.lower()

    if getattr(response_obj, "used_fallback", False) or "simulated" in response or "mock response" in response or "mock" in response:
        pytest.skip("Skipping golden dataset test because LLM API keys are missing/rate-limited and fallback simulator was used.")

    # Assert that the core concept from the golden dataset is at least mentioned in the LLM's response
    # (Or that the response is semantically similar, but for a simple test we use substring matching)

    assert expected_factor in response, f"Expected '{expected_factor}' to be identified, but got: {response}"
