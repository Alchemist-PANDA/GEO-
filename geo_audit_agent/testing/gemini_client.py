import httpx
import time
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class RateLimitError(Exception):
    pass

class APIError(Exception):
    pass

async def generate_content_async(
    prompt: str,
    model: str,
    api_key: str,
    timeout: float = 45.0
) -> Tuple[str, Dict[str, Any]]:
    """
    Asynchronously calls the Google Gemini/Gemma REST API to generate content.
    Returns a tuple of (response_text, raw_result_dict).
    Raises RateLimitError for HTTP 429, and APIError for other failures.
    """
    # Normalize model name for the REST endpoint
    normalized_model = model
    if not model.startswith("models/"):
        normalized_model = f"models/{model}"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{normalized_model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2
        }
    }
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(url, headers=headers, json=data)
            
            if response.status_code == 429:
                raise RateLimitError("Gemini API rate limit exceeded (HTTP 429).")
            
            if response.status_code != 200:
                raise APIError(f"Gemini API returned status {response.status_code}: {response.text}")
            
            result = response.json()
            
            # Extract response text safely
            try:
                candidates = result.get("candidates", [])
                if not candidates:
                    raise APIError("No candidates returned from Gemini model.")
                
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    # Check finishReason (could be safety, block, etc.)
                    finish_reason = candidates[0].get("finishReason")
                    if finish_reason:
                        raise APIError(f"Model stopped generating. Reason: {finish_reason}")
                    raise APIError("Empty parts list returned from Gemini model.")
                
                text = parts[0].get("text", "")
                return text, result
                
            except (KeyError, IndexError) as e:
                raise APIError(f"Failed to parse response structure: {e}. Raw response: {result}")
                
        except httpx.RequestError as e:
            raise APIError(f"Network error during API call: {e}")
