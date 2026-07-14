import pytest

from geo_audit_agent.providers import ExecutionMode, ProviderUnavailableError
from geo_audit_agent.providers.adapters import FixtureAdapter, OpenAICompatibleAdapter, get_provider_adapter


def test_fixture_adapter_is_explicitly_labeled():
    result = FixtureAdapter("openai", "fixture", "demo").query("prompt", prompt_id="p", prompt_version="1")
    assert result.mode is ExecutionMode.FIXTURE
    assert "not a provider response" in result.metadata["disclosure"]


@pytest.mark.parametrize("provider,env_name", [
    ("openai", "OPENAI_API_KEY"), ("perplexity", "PERPLEXITY_API_KEY"),
    ("google", "GOOGLE_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY"),
])
def test_missing_credentials_fail_without_fixture_fallback(monkeypatch, provider, env_name):
    monkeypatch.delenv(env_name, raising=False)
    with pytest.raises(ProviderUnavailableError):
        get_provider_adapter(provider).query("prompt", prompt_id="p", prompt_version="1")


def test_unsupported_provider_fails_explicitly():
    with pytest.raises(ProviderUnavailableError):
        get_provider_adapter("meta")


class _Response:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def _openai_adapter():
    return OpenAICompatibleAdapter("openai", "model", "OPENAI_API_KEY", "https://provider.test/chat")


def test_openai_compatible_success_preserves_evidence_metadata(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "configured-in-test")
    monkeypatch.setattr("geo_audit_agent.providers.adapters.requests.post", lambda *args, **kwargs: _Response(
        payload={"choices": [{"message": {"content": "Acme"}}],
                 "usage": {"prompt_tokens": 4, "completion_tokens": 2}}
    ))
    result = _openai_adapter().query("prompt", prompt_id="p", prompt_version="3")
    assert result.mode is ExecutionMode.LIVE
    assert result.prompt_version == "3"
    assert result.input_tokens == 4
    assert result.output_tokens == 2


def test_openai_compatible_auth_error_is_explicit(monkeypatch):
    from geo_audit_agent.providers import ProviderAuthError
    monkeypatch.setenv("OPENAI_API_KEY", "configured-in-test")
    monkeypatch.setattr("geo_audit_agent.providers.adapters.requests.post",
                        lambda *args, **kwargs: _Response(status_code=401))
    with pytest.raises(ProviderAuthError):
        _openai_adapter().query("prompt", prompt_id="p", prompt_version="1")


def test_openai_compatible_malformed_response_is_explicit(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "configured-in-test")
    monkeypatch.setattr("geo_audit_agent.providers.adapters.requests.post",
                        lambda *args, **kwargs: _Response(payload={"unexpected": True}))
    with pytest.raises(ProviderUnavailableError, match="malformed"):
        _openai_adapter().query("prompt", prompt_id="p", prompt_version="1")
