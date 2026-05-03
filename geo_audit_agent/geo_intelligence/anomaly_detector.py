import os
import json
import logging
from typing import List, Dict
from google import genai
from sentence_transformers import SentenceTransformer
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

# Initialize local embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def query_llms_for_anomalies(queries: List[str], client: genai.Client):
    """Queries Gemini to find cited brands for a list of queries."""
    results = {}
    for query in queries:
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"List top 5 {query}. Return ONLY names as a comma-separated list."
            )
            results[query] = [name.strip() for name in response.text.split(",")]
        except Exception as e:
            logger.error(f"Anomaly query failed for '{query}': {e}")
            results[query] = []
    return results

def check_factual_correctness(brand_name: str, expected_city: str, expected_category: str, client: genai.Client):
    """Uses LLM as a factual verifier."""
    prompt = f"Does the brand '{brand_name}' exist in '{expected_city}'? Is it a '{expected_category}'? Answer with 'Correct' or 'Incorrect' and a short explanation."
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        is_correct = "Correct" in response.text
        return is_correct, response.text
    except Exception as e:
        logger.error(f"Factual check failed for {brand_name}: {e}")
        return False, "Verification failed"

def compute_semantic_similarity(brand_description: str, query: str):
    """Computes cosine similarity between brand description and search query."""
    embeddings = embedding_model.encode([brand_description, query])
    dot_product = np.dot(embeddings[0], embeddings[1])
    norm_a = np.linalg.norm(embeddings[0])
    norm_b = np.linalg.norm(embeddings[1])
    return float(dot_product / (norm_a * norm_b))

def flag_anomalies(audit_results: Dict, city: str, category: str, client: genai.Client):
    """Identifies and logs citation anomalies."""
    anomalies = []
    cited_brands = audit_results.get("cited_brands", [])

    for brand in cited_brands:
        is_correct, explanation = check_factual_correctness(brand, city, category, client)
        if not is_correct:
            anomalies.append({
                "brand": brand,
                "type": "Fact Inconsistency",
                "explanation": explanation
            })

    # Log to file
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    log_file = os.path.join(data_dir, "anomalies_log.json")

    log_entry = {
        "timestamp": os.path.getmtime(log_file) if os.path.exists(log_file) else 0, # Placeholder
        "city": city,
        "category": category,
        "anomalies": anomalies
    }

    try:
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                history = json.load(f)
        else:
            history = []
        history.append(log_entry)
        with open(log_file, "w") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to log anomalies: {e}")

    return anomalies
