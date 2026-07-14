"""Per-agent success metrics. Runtime metrics are deterministic; golden-set
metrics may use DeepEval's LLM-judge metrics."""


def runtime_scores(agent_id: str, output: dict, ctx: dict) -> dict:
    text = output.get("text", "")
    evidence = ctx.get("bundle", {}).get("evidence", [])
    return {
        "has_evidence": 1.0 if evidence else 0.0,
        "length_ok": 1.0 if 10 <= len(text) <= 6000 else 0.0,
        "cited_numbers": 1.0 if any(c.isdigit() for c in text) else 0.0,
        "no_leak": 0.0 if "system prompt" in text.lower() else 1.0,
    }


def aggregate(scores: dict) -> float:
    return round(sum(scores.values()) / max(len(scores), 1), 3)
