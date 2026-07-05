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

def get_redis_client():
    """Return Redis client or None if not configured."""
    if not REDIS_MODULE_AVAILABLE:
        logger.info("redis package not installed – using in-memory cache fallback.")
        return None
    import os
    redis_url = None
    try:
        import streamlit as st
        redis_url = st.secrets.get("redis_url")
    except Exception:
        pass
    if not redis_url:
        redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        logger.info("Redis URL not configured – using in-memory cache fallback.")
        return None

    try:
        client = redis.from_url(redis_url, socket_timeout=2.0)  # type: ignore
        client.ping()
        logger.info("Connected to Redis caching server successfully.")
        return client
    except Exception as e:
        logger.warning(f"Redis connection failed (using in-memory fallback): {e}")
        return None

r = get_redis_client()
REDIS_AVAILABLE = r is not None

def get_cache_key(tier: str, prompt: str) -> str:
    payload = json.dumps({"tier": tier, "prompt": prompt}, sort_keys=True)
    return f"geo:cache:{hashlib.md5(payload.encode()).hexdigest()}"

def get_cached_response(tier: str, prompt: str) -> Optional[str]:
    key = get_cache_key(tier, prompt)
    if REDIS_AVAILABLE:
        try:
            assert r is not None
            val = r.get(key)
            if val:
                if isinstance(val, bytes):
                    return val.decode("utf-8")
                return val
        except Exception as e:
            logger.warning(f"Failed to read from Redis cache: {e}")
    return IN_MEMORY_CACHE.get(key)

def set_cached_response(tier: str, prompt: str, response: str, ttl: int = 86400) -> None:
    key = get_cache_key(tier, prompt)
    if REDIS_AVAILABLE:
        try:
            assert r is not None
            r.setex(key, ttl, response)
            return
        except Exception as e:
            logger.warning(f"Failed to write to Redis cache: {e}")
    IN_MEMORY_CACHE[key] = response
