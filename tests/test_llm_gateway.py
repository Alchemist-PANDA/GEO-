import os
os.environ["FORCE_MOCK"] = "true"

from geo_audit_agent.llm.gateway import claude, router, parse_json, _mock


def test_mock_returns_result():
    r = _mock("hello", "test")
    assert r.provider == "mock"
    assert "mock" in r.text


def test_claude_mock_mode():
    r = claude("system", "user message")
    assert r.provider == "mock"
    assert r.text


def test_router_mock_mode():
    r = router("test prompt")
    assert r.provider == "mock"


def test_parse_json_valid():
    assert parse_json('{"key": "value"}') == {"key": "value"}


def test_parse_json_wrapped():
    assert parse_json('Here is the result: {"key": "value"} done') == {"key": "value"}


def test_parse_json_invalid():
    assert parse_json("not json at all") == {}


def test_parse_json_empty():
    assert parse_json("") == {}
