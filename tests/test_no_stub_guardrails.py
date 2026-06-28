import inspect
from geo_audit_agent.guardrails import handlers as H

def test_security_phase_not_stubbed():
    src = inspect.getsource(H.security_guardrail)
    assert "_todo" not in src, "security_guardrail is still a fail-open stub"

def test_workflow_phase_not_stubbed():
    src = inspect.getsource(H.workflow_guardrail)
    assert "_todo" not in src, "workflow_guardrail is still a fail-open stub"

def test_retrieval_phase_not_stubbed():
    src = inspect.getsource(H.retrieval_guardrail)
    assert "_todo" not in src, "retrieval_guardrail is still a fail-open stub"
