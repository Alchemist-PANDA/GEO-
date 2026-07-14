import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from geo_audit_agent.api.auth import identity_from_token, require_admin


def _token(secret: str, sub: str = "user-1", role: str | None = None) -> str:
    payload = {"sub": sub}
    if role:
        payload["app_metadata"] = {"role": role}
    return jwt.encode(payload, secret, algorithm="HS256")


def test_identity_comes_from_verified_token(monkeypatch):
    secret = "test-secret-that-is-at-least-32-bytes"
    monkeypatch.setenv("SUPABASE_JWT_SECRET", secret)
    assert identity_from_token(_token(secret)) == "user-1"


def test_admin_dependency_rejects_normal_user(monkeypatch):
    secret = "test-secret-that-is-at-least-32-bytes"
    monkeypatch.setenv("SUPABASE_JWT_SECRET", secret)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=_token(secret))
    with pytest.raises(HTTPException) as error:
        require_admin(credentials)
    assert error.value.status_code == 403


def test_admin_dependency_accepts_signed_admin_claim(monkeypatch):
    secret = "test-secret-that-is-at-least-32-bytes"
    monkeypatch.setenv("SUPABASE_JWT_SECRET", secret)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=_token(secret, role="admin"))
    assert require_admin(credentials) == "user-1"
