import logging
from typing import Any

try:
    import httpx
except ImportError:  # Optional until a live validation run is requested.
    httpx = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

class RateLimitError(Exception):
    pass

class APIError(Exception):
    pass

async def generate_content_async(
    prompt: str,
    model: str,
    api_key: str,
    timeout: float = 45.0,
    max_output_tokens: int = 512,
    temperature: float = 0.0,
) -> tuple[str, dict[str, Any]]:
    """
    Asynchronously calls the Google Gemini/Gemma REST API to generate content.
    Returns a tuple of (response_text, raw_result_dict).
    Raises RateLimitError for HTTP 429, and APIError for other failures.
    """
    # Normalize model name for the REST endpoint
    if httpx is None:
        raise APIError("httpx is not installed; install runtime requirements before live validation")
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
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        }
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = None
        error_msg = None
        try:
            try:
                response = await client.post(url, headers=headers, json=data)
            except Exception as e:
                error_msg = str(e)
                raise

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
                raise APIError(f"Failed to parse response structure: {e}. Raw response: {result}") from e

        except httpx.RequestError as e:
            raise APIError(f"Network error during API call: {e}") from e
        finally:
            import datetime
            import json
            import os
            # Never persist prompts, responses, URLs containing credentials, or
            # exception bodies. Validation runs can contain customer data.
            log_record = {
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "request": {
                    "url": url.split("?key=")[0] + "?key=MASKED",
                    "model": model,
                    "prompt_chars": len(prompt),
                },
                "response": {
                    "status_code": response.status_code if response else None,
                    "response_chars": len(response.text) if response else 0,
                "error_type": "request_error" if error_msg else None,
                }
            }
            try:
                os.makedirs("data", exist_ok=True)
                with open("data/raw_audit_log.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_record) + "\n")
            except Exception as le:
                logger.error(f"Failed to write to raw_audit_log.jsonl: {le}")
