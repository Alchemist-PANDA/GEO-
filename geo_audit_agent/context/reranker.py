"""Rerank top-20 → top-5 with BGE cross-encoder."""
import os

_reranker = None


def _load():
    global _reranker
    if _reranker is None and os.getenv("FORCE_MOCK") != "true":
        from FlagEmbedding import FlagReranker
        _reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)
    return _reranker


def rerank(query: str, docs: list[dict], top_n: int = 5) -> list[dict]:
    if not docs:
        return []
    rr = _load()
    if rr is None:
        return docs[:top_n]
    scores = rr.compute_score([[query, d["text"]] for d in docs])
    for d, s in zip(docs, scores if isinstance(scores, list) else [scores], strict=False):
        d["rerank_score"] = float(s)
    return sorted(docs, key=lambda d: d["rerank_score"], reverse=True)[:top_n]
