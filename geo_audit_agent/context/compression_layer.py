import logging

logger = logging.getLogger(__name__)


def _fit_to_budget(texts: list[str], token_budget: int) -> list[str]:
    """Keep evidence items in order until the (~4 chars/token) budget is spent."""
    out: list[str] = []
    used = 0
    for t in texts:
        used += len(t) // 4
        if used > token_budget:
            break
        out.append(t)
    return out


def compress(bundle: dict, token_budget: int = 6000) -> dict:
    seen, deduped = set(), []
    for txt in bundle["evidence"]:
        key = txt[:120]
        if key not in seen:
            seen.add(key)
            deduped.append(txt)
    kept = _fit_to_budget(deduped, token_budget)
    if len(kept) < len(deduped):
        logger.info("Context compression dropped %d evidence items to fit %d-token budget",
                    len(deduped) - len(kept), token_budget)
    bundle["evidence"] = kept
    return bundle
