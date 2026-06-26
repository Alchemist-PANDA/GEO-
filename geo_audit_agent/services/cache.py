# cache.py
try:
    import redis
    REDIS_MODULE_AVAILABLE = True
except ImportError:
    REDIS_MODULE_AVAILABLE = False

import logging
import hashlib
import json
from typing import Optional

logger = logging.getLogger(__name__)

# Fallback in-memory cache to support local testing without a live Redis container
IN_MEMORY_CACHE: dict[str, str] = {}

REDIS_AVAILABLE = False
r = None

if REDIS_MODULE_AVAILABLE:
    try:
        # Attempt to initialize Redis connection pool
        pool = redis.ConnectionPool(host="localhost", port=6379, db=0, socket_timeout=2.0)  # type: ignore[name-defined]
        r = redis.Redis(connection_pool=pool)  # type: ignore[name-defined]
        r.ping()
        REDIS_AVAILABLE = True
        logger.info("Connected to Redis caching server successfully.")
    except Exception as e:
        logger.warning(f"Redis is not available (using in-memory fallback): {e}")
else:
    logger.info("redis package not installed – using in-memory cache fallback.")

def get_cache_key(tier: str, prompt: str) -> str:
    payload = json.dumps({"tier": tier, "prompt": prompt}, sort_keys=True)
    return f"geo:cache:{hashlib.md5(payload.encode()).hexdigest()}"

def get_cached_response(tier: str, prompt: str) -> Optional[str]:
    key = get_cache_key(tier, prompt)
    if REDIS_AVAILABLE:
        try:
            val = r.get(key)  # type: ignore
            if val:
                return val.decode("utf-8")  # type: ignore
        except Exception as e:
            logger.warning(f"Failed to read from Redis cache: {e}")
    return IN_MEMORY_CACHE.get(key)

def set_cached_response(tier: str, prompt: str, response: str, ttl: int = 86400) -> None:
    key = get_cache_key(tier, prompt)
    if REDIS_AVAILABLE:
        try:
            r.setex(key, ttl, response)
            return
        except Exception as e:
            logger.warning(f"Failed to write to Redis cache: {e}")
    IN_MEMORY_CACHE[key] = response
