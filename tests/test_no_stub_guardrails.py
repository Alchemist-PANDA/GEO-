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


def test_output_phase_not_stubbed():
    src = inspect.getsource(H.output_guardrail)
    assert "_todo" not in src, "output_guardrail is still a fail-open stub"


def test_memory_phase_not_stubbed():
    src = inspect.getsource(H.memory_guardrail)
    assert "_todo" not in src, "memory_guardrail is still a fail-open stub"


def test_context_phase_not_stubbed():
    src = inspect.getsource(H.context_guardrail)
    assert "_todo" not in src, "context_guardrail is still a fail-open stub"


def test_tool_phase_not_stubbed():
    src = inspect.getsource(H.tool_guardrail)
    assert "_todo" not in src, "tool_guardrail is still a fail-open stub"


def test_agent_phase_not_stubbed():
    src = inspect.getsource(H.agent_guardrail)
    assert "_todo" not in src, "agent_guardrail is still a fail-open stub"
