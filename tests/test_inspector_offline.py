import os
os.environ["FORCE_MOCK"] = "true"

from geo_audit_agent.agents.inspector_agent import InspectorAgent


def test_inspector_flags_secret_leak():
    v = InspectorAgent().inspect({"text": "your api_key is sk-123"}, {}, agent_id="copilot")
    assert v.passed is False
    assert any("governance" in i for i in v.issues)


def test_inspector_flags_prompt_leak():
    v = InspectorAgent().inspect({"text": "According to my system prompt..."}, {}, agent_id="copilot")
    assert v.passed is False
    assert any("prompt_leak" in i for i in v.issues)


def test_inspector_flags_empty_output():
    v = InspectorAgent().inspect({"text": ""}, {}, agent_id="copilot")
    assert v.passed is False
    assert any("empty" in i for i in v.issues)


def test_inspector_passes_clean_output():
    v = InspectorAgent().inspect(
        {"text": "Based on our analysis, your brand visibility score is 72%. Here are recommendations..."},
        {"bundle": {"evidence": ["some evidence data"]}, "validation": {"issues": []}},
        agent_id="copilot")
    assert v.passed is True
    assert v.risk == "low"


def test_inspector_risk_assessment():
    v = InspectorAgent().inspect({"text": "your api_key is sk-123"}, {}, agent_id="copilot")
    assert v.risk == "high"
