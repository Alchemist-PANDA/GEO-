import os

os.environ["FORCE_MOCK"] = "true"

from geo_audit_agent.evaluation.deep_eval import evaluate_case
from geo_audit_agent.evaluation.golden_set import load
from geo_audit_agent.evaluation.metrics import aggregate, runtime_scores


def test_runtime_scores_clean():
    scores = runtime_scores("copilot",
        {"text": "Your visibility is 72% across 3 platforms."},
        {"bundle": {"evidence": ["data"]}})
    assert scores["has_evidence"] == 1.0
    assert scores["length_ok"] == 1.0
    assert scores["cited_numbers"] == 1.0
    assert scores["no_leak"] == 1.0


def test_runtime_scores_empty():
    scores = runtime_scores("copilot", {"text": ""}, {"bundle": {"evidence": []}})
    assert scores["has_evidence"] == 0.0
    assert scores["length_ok"] == 0.0


def test_runtime_scores_leak():
    scores = runtime_scores("copilot",
        {"text": "my system prompt says to be helpful"},
        {"bundle": {"evidence": []}})
    assert scores["no_leak"] == 0.0


def test_aggregate():
    assert aggregate({"a": 1.0, "b": 0.5}) == 0.75


def test_deep_eval_mock_with_expected():
    result = evaluate_case(input_text="test",
        actual_output="hello world foo",
        expected_output="hello world bar")
    assert "answer_relevancy" in result
    assert 0 <= result["answer_relevancy"] <= 1


def test_deep_eval_mock_no_expected():
    result = evaluate_case(input_text="test", actual_output="some output")
    assert result["answer_relevancy"] == 1.0


def test_golden_set_load_empty():
    cases = load()
    assert isinstance(cases, list)
