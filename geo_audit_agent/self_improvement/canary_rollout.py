"""Versioned config in Redis. 5% traffic → variant; instant rollback flag.
Execution-Agent changes ALWAYS require human approval (no auto-promote)."""
import os
import json
import hashlib
import redis
_r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

def set_canary(agent_id, proposal_id, payload, pct=5):
    _r.set(f"canary:{agent_id}", json.dumps(
        {"proposal_id": proposal_id, "payload": payload, "pct": pct}))

def variant_active(agent_id, request_key: str) -> dict | None:
    raw = _r.get(f"canary:{agent_id}")
    if not raw:
        return None
    cfg = json.loads(raw)
    bucket = int(hashlib.md5(request_key.encode()).hexdigest()[:8], 16) % 100
    return cfg if bucket < cfg["pct"] else None

def promote(agent_id):   
    _r.set(f"config:{agent_id}", _r.get(f"canary:{agent_id}"))
    _r.delete(f"canary:{agent_id}")
def rollback(agent_id):  
    _r.delete(f"canary:{agent_id}")     # instant revert to stable
