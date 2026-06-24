import time
import logging
from typing import Tuple, Dict, Optional
import redis
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
        self.redis: Optional[redis.Redis] = None
        try:
            self.redis = redis.Redis(host=host, port=port, db=db, socket_timeout=3)
        except Exception as e:
            logger.error(f"Redis rate limiter connection failed: {e}")

    def is_allowed(self, client_key: str) -> Tuple[bool, Dict[str, str]]:
        now = int(time.time())
        if not self.redis:
            return True, {}

        key = f"rate_limit:{client_key}"
        try:
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, now - self.window)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, self.window)
            _, count, _, _ = pipe.execute()

            remaining = max(0, self.limit - count)
            headers = {
                "X-RateLimit-Limit": str(self.limit),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(now + self.window),
            }

            if count > self.limit:
                headers["Retry-After"] = str(self.window)
                return False, headers

            return True, headers
        except redis.RedisError as e:
            logger.error(f"Rate limiter error: {e}")
            return True, {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limiter: RedisRateLimiter):
        super().__init__(app)
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in ("/health", "/ready", "/v1/docs", "/v1/redoc"):
            return await call_next(request)

        user_id = request.headers.get("X-User-ID")
        client_key = user_id or (request.client.host if request.client else "127.0.0.1")

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
