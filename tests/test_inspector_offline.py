import os
os.environ["FORCE_MOCK"] = "true"
from geo_audit_agent.agents.inspector_agent import InspectorAgent

def test_inspector_flags_secret_leak():
    v = InspectorAgent().inspect({"text": "your api_key is sk-123"}, {}, agent_id="copilot")
    assert v.passed is False
    assert any("governance" in i for i in v.issues)

def test_inspector_allows_clean_output():
    v = InspectorAgent().inspect({"text": "This is a clean response with sufficient content."}, {}, agent_id="copilot")
    assert v.passed is True
    assert len(v.issues) == 0

def test_inspector_flags_empty_output():
    v = InspectorAgent().inspect({"text": ""}, {}, agent_id="copilot")
    assert v.passed is False
    assert any("output_quality:empty" in i for i in v.issues)
