# cache.py
import hashlib
import json
import logging

import redis

logger = logging.getLogger(__name__)

# Fallback in-memory cache to support local testing without a live Redis container
IN_MEMORY_CACHE: dict[str, str] = {}

REDIS_AVAILABLE = False
_redis_client = None

def _get_redis():
    global REDIS_AVAILABLE, _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import os
        pool = redis.ConnectionPool(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=0,
            socket_timeout=2.0,
        )
        client = redis.Redis(connection_pool=pool)
        client.ping()
        _redis_client = client
        REDIS_AVAILABLE = True
        logger.info("Connected to Redis caching server successfully.")
    except Exception as e:
        REDIS_AVAILABLE = False
        logger.warning("Redis is not available (using in-memory fallback): %s", e)
    return _redis_client

def get_cache_key(tier: str, prompt: str) -> str:
    payload = json.dumps({"tier": tier, "prompt": prompt}, sort_keys=True)
    return f"geo:cache:{hashlib.md5(payload.encode()).hexdigest()}"

def _record_cache_op(operation: str) -> None:
    try:
        from geo_audit_agent.observability.metrics import CACHE_OPERATIONS
        CACHE_OPERATIONS.labels(operation=operation).inc()
    except Exception:
        pass


def get_cached_response(tier: str, prompt: str) -> str | None:
    key = get_cache_key(tier, prompt)
    client = _get_redis()
    if client is not None:
        try:
            val = client.get(key)
            if val:
                _record_cache_op("hit")
                return val.decode("utf-8")
        except Exception as e:
            logger.warning("Failed to read from Redis cache: %s", e)
            _record_cache_op("error")
    result = IN_MEMORY_CACHE.get(key)
    _record_cache_op("hit" if result is not None else "miss")
    return result

def set_cached_response(tier: str, prompt: str, response: str, ttl: int = 86400) -> None:
    key = get_cache_key(tier, prompt)
    client = _get_redis()
    if client is not None:
        try:
            client.setex(key, ttl, response)
            return
        except Exception as e:
            logger.warning("Failed to write to Redis cache: %s", e)
    IN_MEMORY_CACHE[key] = response
