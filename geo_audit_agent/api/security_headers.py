"""Security-headers middleware + optional /metrics auth.

Adds the standard hardening headers every response should carry (defense
against clickjacking, MIME sniffing, and TLS downgrade), and a tiny guard
that gates the Prometheus /metrics endpoint behind a bearer token when
``METRICS_TOKEN`` is configured (no token set => open, preserving current
local-dev behaviour).
"""
from __future__ import annotations

import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Conservative header set. CSP is intentionally strict-but-API-friendly: the
# JSON API serves no HTML, so 'none' default-src is safe and blocks any
# accidental script execution in error pages / docs proxies.
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

# Swagger/redoc need to load their own inline assets, so relax CSP there only.
_DOCS_PATHS = ("/v1/docs", "/v1/redoc", "/v1/openapi.json")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for key, value in _SECURITY_HEADERS.items():
            if key == "Content-Security-Policy" and request.url.path in _DOCS_PATHS:
                continue
            response.headers.setdefault(key, value)
        return response


class MetricsAuthMiddleware(BaseHTTPMiddleware):
    """Require a bearer token for /metrics when METRICS_TOKEN is set."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path.rstrip("/") == "/metrics":
            token = os.getenv("METRICS_TOKEN")
            if token:
                header = request.headers.get("Authorization", "")
                if header != f"Bearer {token}":
                    return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        return await call_next(request)
