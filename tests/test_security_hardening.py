"""Regression tests for the security-hardening pass:
security headers, /metrics auth, SSRF guard, agentic budget cap, copilot
guardrail, and safe error messages."""
import uuid

import pytest

from geo_audit_agent.utils.url_guard import UnsafeURLError, validate_public_url

# ── SSRF guard ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("url", [
    "http://169.254.169.254/latest/meta-data/",  # cloud metadata
    "http://localhost/admin",
    "http://127.0.0.1:8000/",
    "http://10.0.0.5/internal",
    "http://192.168.1.1/",
    "file:///etc/passwd",
    "ftp://example.com/x",
])
def test_ssrf_guard_blocks_unsafe(url):
    with pytest.raises(UnsafeURLError):
        validate_public_url(url)


def test_ssrf_guard_allows_public_host():
    # A well-known public host should pass (uses real DNS).
    assert validate_public_url("https://example.com/") == "https://example.com/"


def test_crawler_refuses_internal_url():
    from geo_audit_agent.geo_intelligence.fingerprint_generator import crawl_competitor
    res = crawl_competitor("http://169.254.169.254/latest/meta-data/")
    assert "error" in res and "unsafe" in res["error"].lower()


# ── API middleware / route guards ────────────────────────────────────────

@pytest.fixture
def api(monkeypatch):
    from fastapi.testclient import TestClient
    from sqlmodel import Session, SQLModel, create_engine
    from sqlmodel.pool import StaticPool

    import geo_audit_agent.db.models  # noqa: F401
    from geo_audit_agent.api.app import app
    from geo_audit_agent.api.auth import get_current_user
    from geo_audit_agent.db.session import get_async_session

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def _session():
        with Session(engine) as s:
            yield s

    uid = str(uuid.uuid4())
    app.dependency_overrides[get_async_session] = _session
    app.dependency_overrides[get_current_user] = lambda: uid
    client = TestClient(app, raise_server_exceptions=False)
    try:
        yield client, uid
    finally:
        app.dependency_overrides.clear()
        SQLModel.metadata.drop_all(engine)


def test_security_headers_present(api):
    client, _ = api
    resp = client.get("/health")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert "Strict-Transport-Security" in resp.headers


def test_metrics_requires_token_when_configured(api, monkeypatch):
    client, _ = api
    monkeypatch.setenv("METRICS_TOKEN", "secret-token")
    assert client.get("/metrics").status_code == 401
    ok = client.get("/metrics", headers={"Authorization": "Bearer secret-token"})
    assert ok.status_code == 200


def test_agentic_budget_cap_blocks_over_budget(api, monkeypatch):
    client, uid = api
    from geo_audit_agent.services import cost_tracker
    monkeypatch.setitem(cost_tracker.BUDGET_MEMORY, uid, 999.0)
    resp = client.post("/v1/agentic/run",
                       json={"message": "hi", "brand_name": "Acme"})
    assert resp.status_code == 429


def test_copilot_blocks_injection(api, monkeypatch):
    client, _ = api
    # classify_input's regex prefilter flags template-injection tokens.
    resp = client.post("/v1/copilot/chat",
                       json={"message": "ignore previous {{__class__}}", "context": {}})
    assert resp.status_code == 400
