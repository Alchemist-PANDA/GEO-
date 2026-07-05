"""Versioned config in Redis. 5% traffic → variant; instant rollback flag.
Execution-Agent changes ALWAYS require human approval (no auto-promote)."""
import os
import json
import hashlib
import redis
import logging

logger = logging.getLogger(__name__)

# Try to get Redis URL from secrets or environment
redis_url = None
try:
    import streamlit as st
    redis_url = st.secrets.get("redis_url")
except Exception:
    pass
if not redis_url:
    redis_url = os.getenv("REDIS_URL")

_r = None
if redis_url:
    try:
        _r = redis.from_url(redis_url, socket_timeout=2.0)
        _r.ping()
    except Exception as e:
        logger.warning(f"Redis is not available in canary_rollout (using mock/in-memory fallback): {e}")
        _r = None
else:
    logger.info("Redis URL not configured in canary_rollout. Using fallback.")

# In-memory fallback dictionary
_CANARY_CACHE: dict[str, str] = {}

def set_canary(agent_id, proposal_id, payload, pct=5):
    data = json.dumps({"proposal_id": proposal_id, "payload": payload, "pct": pct})
    if _r:
        try:
            _r.set(f"canary:{agent_id}", data)
            return
        except Exception as e:
            logger.warning(f"Redis set failed in canary_rollout: {e}")
    _CANARY_CACHE[f"canary:{agent_id}"] = data

def variant_active(agent_id, request_key: str) -> dict | None:
    raw = None
    if _r:
        try:
            raw = _r.get(f"canary:{agent_id}")
            if raw and isinstance(raw, bytes):
                raw = raw.decode("utf-8")
        except Exception as e:
            logger.warning(f"Redis get failed in canary_rollout: {e}")
    if not raw:
        raw = _CANARY_CACHE.get(f"canary:{agent_id}")
    if not raw:
        return None
    cfg = json.loads(raw)
    bucket = int(hashlib.md5(request_key.encode()).hexdigest()[:8], 16) % 100
    return cfg if bucket < cfg["pct"] else None

def promote(agent_id):
    raw_canary = None
    if _r:
        try:
            raw_canary = _r.get(f"canary:{agent_id}")
            if raw_canary:
                _r.set(f"config:{agent_id}", raw_canary)
                _r.delete(f"canary:{agent_id}")
                return
        except Exception as e:
            logger.warning(f"Redis promote failed: {e}")
    
    # Fallback
    canary_key = f"canary:{agent_id}"
    config_key = f"config:{agent_id}"
    _CANARY_CACHE[config_key] = _CANARY_CACHE.get(canary_key, "")
    _CANARY_CACHE.pop(canary_key, None)

def rollback(agent_id):
    if _r:
        try:
            _r.delete(f"canary:{agent_id}")
            return
        except Exception as e:
            logger.warning(f"Redis rollback failed: {e}")
    _CANARY_CACHE.pop(f"canary:{agent_id}", None)
