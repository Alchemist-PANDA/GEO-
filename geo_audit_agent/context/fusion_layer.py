def fuse(*, query: str, retrieved: list[dict], memory: list[dict],
         business_rules: list[str], live_metrics: dict, history: list[dict],
         agent_state: dict) -> dict:
    """Merge all context sources into one structured bundle (no LLM)."""
    return {
        "query": query,
        "evidence": [d["text"] for d in retrieved],
        "evidence_meta": [d["meta"] for d in retrieved],
        "memory": memory,
        "business_rules": business_rules,
        "live_metrics": live_metrics,
        "history": history[-6:],             # last 3 turns
        "agent_state": agent_state,
    }
