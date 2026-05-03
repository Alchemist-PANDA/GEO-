import json
import os
import chromadb
from chromadb.utils import embedding_functions

def save_fingerprint_json(fingerprint: dict):
    """Saves fingerprint to data directory."""
    data_dir = "data/fingerprints"
    os.makedirs(data_dir, exist_ok=True)
    filename = f"{fingerprint['brand_name'].lower().replace(' ', '_')}.json"
    with open(os.path.join(data_dir, filename), "w") as f:
        json.dump(fingerprint, f, indent=4)

def store_in_vector_db(fingerprint: dict):
    """Stores fingerprint keywords in ChromaDB for similarity search."""
    client = chromadb.PersistentClient(path="data/chroma_db")
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = client.get_or_create_collection(name="brand_fingerprints", embedding_function=sentence_transformer_ef)

    # Join keywords into a single string for embedding
    content = " ".join(fingerprint.get("keywords", []))
    collection.upsert(
        documents=[content],
        metadatas=[{"brand": fingerprint["brand_name"], "url": fingerprint["url"]}],
        ids=[fingerprint["brand_name"]]
    )

def search_similar_brands(query_text: str, n_results=3):
    """Finds brands with similar semantic fingerprints."""
    client = chromadb.PersistentClient(path="data/chroma_db")
    collection = client.get_collection(name="brand_fingerprints")
    results = collection.query(query_texts=[query_text], n_results=n_results)
    return results
