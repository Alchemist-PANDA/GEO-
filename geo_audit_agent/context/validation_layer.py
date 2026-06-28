def validate(bundle: dict, *, min_evidence: int = 1, token_budget: int = 6000) -> dict:
    """Return {valid, issues[]}. Feeds the 'context' guardrail phase."""
    issues = []
    if len(bundle.get("evidence", [])) < min_evidence and bundle["query"]:
        issues.append("insufficient_evidence")
    est_tokens = sum(len(t) for t in bundle.get("evidence", [])) // 4
    if est_tokens > token_budget:
        issues.append("over_token_budget")
    metas = bundle.get("evidence_meta", [])
    if metas and len({m.get("source") for m in metas}) < 2 and len(metas) > 2:
        issues.append("low_source_diversity")
    return {"valid": not any(i in ("over_token_budget",) for i in issues),
            "issues": issues, "bundle": bundle}
