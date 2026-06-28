"""Long-term memory via Mem0, scoped per user_id. Mock-safe in-process store offline."""
import os
_mem, _fallback = None, {}  # type: ignore

def _client():
    global _mem
    if _mem is None and os.getenv("FORCE_MOCK") != "true" and os.getenv("MEM0_BACKEND") != "local":
        try:
            from mem0 import Memory
            _mem = Memory.from_config({"vector_store": {"provider": "qdrant",
                "config": {"url": os.getenv("QDRANT_URL", "http://localhost:6333")}}})
        except Exception:
            _mem = None
    return _mem

def add(user_id: str, text: str, metadata: dict | None = None):
    from geo_audit_agent.memory.memory_guardrails import allow_memory
    ok, reason = allow_memory(text, metadata or {})
    if not ok:
        return {"saved": False, "reason": reason}
    m = _client()
    if m is None:
        _fallback.setdefault(user_id, []).append({"text": text, "meta": metadata or {}})
        return {"saved": True, "backend": "local"}
    m.add(text, user_id=user_id, metadata=metadata or {})
    return {"saved": True, "backend": "mem0"}

def search(user_id: str, query: str, limit: int = 5) -> list[str]:
    m = _client()
    if m is None:
        return [x["text"] for x in _fallback.get(user_id, [])][:limit]
    res = m.search(query, user_id=user_id, limit=limit)
    return [r.get("memory", r.get("text", "")) for r in (res.get("results", res) or [])]
