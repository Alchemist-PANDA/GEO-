import logging
import os
import threading
import time
from collections import defaultdict, deque

try:
    import redis
    REDIS_MODULE_AVAILABLE = True
    from redis import RedisError
except ImportError:
    REDIS_MODULE_AVAILABLE = False
    class RedisError(Exception):  # type: ignore
        pass

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """Sliding-window token bucket. Addresses: Audit 2 §4, PE-OS Law 9."""

    def __init__(self, host: str = "localhost", port: int = 6379,
                 db: int = 1, limit: int = 100, window: int = 3600):
        self.limit = limit
        self.window = window
        self.redis: redis.Redis | None = None
        self._fallback: dict[str, deque[int]] = defaultdict(deque)
        self._fallback_lock = threading.Lock()
        redis_url = None
        try:
            import streamlit as st
            redis_url = st.secrets.get("redis_url")
        except Exception:
            pass
        if not redis_url:
            redis_url = os.getenv("REDIS_URL")

        if REDIS_MODULE_AVAILABLE:
            try:
                if redis_url:
                    self.redis = redis.from_url(redis_url, socket_timeout=3)
                else:
                    self.redis = redis.Redis(host=host, port=port, db=db, socket_timeout=3)  # type: ignore
                self.redis.ping()
            except Exception as e:
                logger.warning("Redis rate limiter unavailable; using process-local limiter: %s", type(e).__name__)
                self.redis = None

    def _local_is_allowed(self, client_key: str, now: int) -> tuple[bool, dict[str, str]]:
        with self._fallback_lock:
            events = self._fallback[client_key]
            while events and events[0] <= now - self.window:
                events.popleft()
            allowed = len(events) < self.limit
            if allowed:
                events.append(now)
            remaining = max(0, self.limit - len(events))
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(now + self.window),
        }
        if not allowed:
            headers["Retry-After"] = str(self.window)
        return allowed, headers

    def is_allowed(self, client_key: str) -> tuple[bool, dict[str, str]]:
        import uuid as _uuid
        now = int(time.time())
        if not self.redis:
            return self._local_is_allowed(client_key, now)

        key = f"rate_limit:{client_key}"
        member = f"{now}:{_uuid.uuid4().hex[:8]}"
        try:
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, now - self.window)
            pipe.zcard(key)
            pipe.zadd(key, {member: now})
            pipe.expire(key, self.window)
            _, count, _, _ = pipe.execute()

            remaining = max(0, self.limit - count)
            headers = {
                "X-RateLimit-Limit": str(self.limit),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(now + self.window),
            }

            if count >= self.limit:
                headers["Retry-After"] = str(self.window)
                return False, headers

            return True, headers
        except RedisError as e:
            logger.error("Redis rate limiter failed; enforcing process-local limit: %s", type(e).__name__)
            return self._local_is_allowed(client_key, now)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limiter: RedisRateLimiter):
        super().__init__(app)
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in ("/health", "/ready", "/v1/docs", "/v1/redoc"):
            return await call_next(request)

        # Never trust caller-controlled identity headers for security controls.
        # The IP fallback is intentionally conservative; authenticated routes still
        # validate the JWT in their dependency.
        client_key = request.client.host if request.client else "unknown"
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            try:
                from geo_audit_agent.api.auth import identity_from_token

                client_key = f"user:{identity_from_token(authorization[7:])}"
            except Exception:
                # Invalid tokens are rejected by protected routes. Rate limiting
                # them by IP prevents forged identities from creating new buckets.
                pass

        allowed, headers = self.limiter.is_allowed(client_key)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers=headers,
            )

        response = await call_next(request)
        for k, v in headers.items():
            response.headers[k] = v
        return response
