import threading
from collections import defaultdict, deque

from geo_audit_agent.api.rate_limiter import RedisRateLimiter


def _local_limiter(limit: int = 2) -> RedisRateLimiter:
    limiter = RedisRateLimiter.__new__(RedisRateLimiter)
    limiter.limit = limit
    limiter.window = 60
    limiter.redis = None
    limiter._fallback = defaultdict(deque)
    limiter._fallback_lock = threading.Lock()
    return limiter


def test_local_fallback_enforces_limit():
    limiter = _local_limiter()
    assert limiter.is_allowed("client")[0] is True
    assert limiter.is_allowed("client")[0] is True
    allowed, headers = limiter.is_allowed("client")
    assert allowed is False
    assert headers["Retry-After"] == "60"


def test_local_fallback_keeps_clients_isolated():
    limiter = _local_limiter(limit=1)
    assert limiter.is_allowed("one")[0] is True
    assert limiter.is_allowed("one")[0] is False
    assert limiter.is_allowed("two")[0] is True
