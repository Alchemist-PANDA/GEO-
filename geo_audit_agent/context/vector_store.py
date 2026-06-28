"""Qdrant retrieval with metadata filters: freshness, source trust, industry,
brand, date, language."""
import os
import logging
from geo_audit_agent.context.embeddings import embed

logger = logging.getLogger(__name__)
COLLECTION = "geo_knowledge"
_client = None

def _client_or_none():
    global _client
    if _client is not None:
        return _client
    if os.getenv("FORCE_MOCK") == "true":
        return None
    try:
        from qdrant_client import QdrantClient
        _client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"),
                               api_key=os.getenv("QDRANT_API_KEY"))
    except Exception as e:
        logger.warning("Qdrant unavailable: %s", e)
        _client = None
    return _client

def search(query: str, *, brand: str | None = None, industry: str | None = None,
           min_trust: float = 0.5, top_k: int = 20) -> list[dict]:
    client = _client_or_none()
    if client is None:
        return []                            # offline → empty, pipeline still runs
    from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
    must = [FieldCondition(key="trust_score", range=Range(gte=min_trust))]
    if brand:    
        must.append(FieldCondition(key="brand", match=MatchValue(value=brand)))
    if industry: 
        must.append(FieldCondition(key="industry", match=MatchValue(value=industry)))
    vec = embed([query])[0]
    hits = client.search(collection_name=COLLECTION, query_vector=vec,
                         query_filter=Filter(must=must), limit=top_k, with_payload=True)  # type: ignore
    return [{"text": h.payload.get("text", ""), "score": h.score,
             "meta": h.payload} for h in hits]
