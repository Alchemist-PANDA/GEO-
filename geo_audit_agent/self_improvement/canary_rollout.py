"""Versioned config in Redis. 5% traffic -> variant; instant rollback flag."""
import hashlib
import json
import logging
import os

logger = logging.getLogger(__name__)
_r = None


def _redis():
    global _r
    if _r is not None:
        return _r
    if os.getenv("FORCE_MOCK") == "true":
        return None
    try:
        import redis
        _r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        _r.ping()
    except Exception as e:
        logger.warning("Redis unavailable for canary rollout: %s", e)
        _r = None
    return _r


def set_canary(agent_id, proposal_id, payload, pct=5):
    r = _redis()
    if r is None:
        return
    r.set(f"canary:{agent_id}", json.dumps(
        {"proposal_id": proposal_id, "payload": payload, "pct": pct}))


def variant_active(agent_id, request_key: str) -> dict | None:
    r = _redis()
    if r is None:
        return None
    raw = r.get(f"canary:{agent_id}")
    if not raw:
        return None
    cfg = json.loads(raw)
    bucket = int(hashlib.md5(request_key.encode(), usedforsecurity=False).hexdigest()[:8], 16) % 100
    return cfg if bucket < cfg["pct"] else None


def promote(agent_id):
    r = _redis()
    if r is None:
        return
    r.set(f"config:{agent_id}", r.get(f"canary:{agent_id}") or "")
    r.delete(f"canary:{agent_id}")


def rollback(agent_id):
    r = _redis()
    if r is None:
        return
    r.delete(f"canary:{agent_id}")
