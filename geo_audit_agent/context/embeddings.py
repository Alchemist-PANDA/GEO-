"""sentence-transformers wrapper, lazy-loaded, mock-safe."""
import os, hashlib
_model = None

def _load():
    global _model
    if _model is None and os.getenv("FORCE_MOCK") != "true":
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _model

def embed(texts: list[str]) -> list[list[float]]:
    model = _load()
    if model is None:                       # deterministic 8-dim mock vector
        return [[int(hashlib.md5((t + str(i)).encode()).hexdigest()[:2], 16) / 255
                 for i in range(8)] for t in texts]
    return model.encode(texts, normalize_embeddings=True).tolist()
