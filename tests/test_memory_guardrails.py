from geo_audit_agent.memory.memory_guardrails import allow_memory


def test_blocks_password():
    ok, reason = allow_memory("my password is hunter2", {})
    assert ok is False
    assert reason == "sensitive_information"


def test_blocks_api_key():
    ok, reason = allow_memory("the api key is abc123", {})
    assert ok is False
    assert reason == "sensitive_information"


def test_blocks_temporary():
    ok, reason = allow_memory("this is loading right now", {})
    assert ok is False
    assert reason == "temporary_information"


def test_blocks_hallucination_risk():
    ok, reason = allow_memory("some fact", {"hallucination_risk": True})
    assert ok is False
    assert reason == "possible_hallucination"


def test_blocks_trivial():
    ok, reason = allow_memory("ok", {})
    assert ok is False
    assert reason == "too_trivial"


def test_allows_valid():
    ok, reason = allow_memory("The brand has 4.5 star rating on Google", {})
    assert ok is True
    assert reason == "ok"
