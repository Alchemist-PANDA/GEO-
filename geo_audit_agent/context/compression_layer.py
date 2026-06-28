from geo_audit_agent.services import context_compression as _cc
def compress(bundle: dict, token_budget: int = 6000) -> dict:
    """Dedup evidence, extract facts, enforce token budget. Reuse existing
    compression util for the heavy lifting; this only orchestrates."""
    seen, deduped = set(), []
    for txt in bundle["evidence"]:
        key = txt[:120]
        if key not in seen:
            seen.add(key); deduped.append(txt)
    bundle["evidence"] = deduped
    # token budgeting via existing util (falls back to char heuristic offline)
    try:
        bundle["evidence"] = _cc.fit_to_budget(deduped, token_budget)
    except Exception:
        joined, out, used = "", [], 0
        for t in deduped:
            used += len(t) // 4
            if used > token_budget: break
            out.append(t)
        bundle["evidence"] = out
    return bundle
