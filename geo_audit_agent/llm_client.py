"""
Shared LLM proxy client for the GEO Audit Agent.
Single source of truth for all LLM API calls.
"""
import os
import json
import logging
import hashlib
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Simple in-memory cache for LLM responses
_llm_cache: Dict[str, str] = {}


def _cache_key(model: str, messages: List[Dict], max_tokens: int, temperature: float) -> str:
    """Generate a deterministic cache key for LLM requests."""
    payload = json.dumps({"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}, sort_keys=True)
    return hashlib.md5(payload.encode()).hexdigest()


def call_proxy_llm(model: str, messages: List[Dict], max_tokens: int = 300, temperature: float = 0.2, use_cache: bool = True) -> str:
    """
    Call the LLM proxy API.

    Args:
        model: The model identifier to use.
        messages: Chat messages in OpenAI format.
        max_tokens: Maximum tokens in the response.
        temperature: Sampling temperature.
        use_cache: Whether to use response caching.

    Returns:
        The LLM response content string.

    Raises:
        EnvironmentError: If required env vars are not set.
        requests.HTTPError: If the API returns an error status.
    """
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    api_key = os.getenv("ANTHROPIC_AUTH_TOKEN")

    if not base_url:
        logger.warning("ANTHROPIC_BASE_URL not set, falling back to localhost proxy.")
        base_url = "http://localhost:20128/v1"

    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_AUTH_TOKEN is not set. "
            "Add it to your .env file: ANTHROPIC_AUTH_TOKEN=your_key_here"
        )

    # Check cache
    if use_cache:
        key = _cache_key(model, messages, max_tokens, temperature)
        if key in _llm_cache:
            logger.debug("LLM cache hit")
            return _llm_cache[key]

    url = f"{base_url}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before=lambda retry_state: logger.info(f"LLM call attempt {retry_state.attempt_number} for model {model}"),
        after=lambda retry_state: logger.error(f"LLM call failed (attempt {retry_state.attempt_number})") if retry_state.outcome and retry_state.outcome.failed else None
    )
    def _do_request():
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        logger.debug(f"Raw LLM response: {content[:200]}")
        return content

    result = _do_request()

    # Store in cache
    if use_cache:
        key = _cache_key(model, messages, max_tokens, temperature)
        _llm_cache[key] = result

    return result
