# llm_router.py
import logging
import os

from google import genai
from google.genai import types

from geo_audit_agent.llm_client import call_proxy_llm
from geo_audit_agent.providers import ProviderUnavailableError

logger = logging.getLogger(__name__)

class LLMProviderResponse:
    def __init__(
        self,
        text: str,
        total_tokens: int = 200,
        cost_usd: float = 0.0001,
        provider: str = "fallback",
        used_fallback: bool = False,
    ):
        self.text = text
        self.total_tokens = total_tokens
        self.cost_usd = cost_usd
        self.provider = provider
        self.used_fallback = used_fallback

def query_provider(prompt: str, tier: str = "balanced", correlation_id: str = "") -> LLMProviderResponse:
    """Routes prompt queries to the appropriate LLM provider depending on the tier constraint."""
    if os.getenv("FORCE_MOCK") == "true":
        return LLMProviderResponse(
            text="mock response: FORCE_MOCK is enabled; no live provider was called.",
            total_tokens=len(prompt.split()),
            cost_usd=0.0,
            provider="mock",
            used_fallback=True,
        )

    api_key = os.getenv("GOOGLE_API_KEY")
    messages = [{"role": "user", "content": prompt}]

    if api_key:
        try:
            logger.info("Routing to Google Gemini API for %s tier (Correlation ID: %s)", tier, correlation_id)
            client = genai.Client(api_key=api_key)

            # Map tier constraints to target models
            model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
            if tier == "deep":
                model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=1000
                )
            )
            text = response.text or ""
            return LLMProviderResponse(
                text=text,
                total_tokens=len(prompt.split()) + len(text.split()),
                cost_usd=0.0001,
                provider="google"
            )
        except Exception as e:
            logger.warning("Google GenAI routing failed: %s", type(e).__name__)
            raise ProviderUnavailableError(f"Google provider failed: {type(e).__name__}") from e

    # The proxy is an explicitly configured provider, not a hidden simulation.
    try:
        logger.info("Routing to fallback legacy proxy client (Correlation ID: %s)", correlation_id)
        text = call_proxy_llm(
            model="gc/gemini-3-flash-preview",
            messages=messages,
            max_tokens=1000,
            temperature=0.2
        )
        return LLMProviderResponse(
            text=text,
            total_tokens=len(prompt.split()) + len(text.split()),
            cost_usd=0.0002,
            provider="proxy_fallback"
        )
    except Exception as e:
        logger.error("Fallback proxy call failed: %s", e)
        raise ProviderUnavailableError(f"Proxy provider failed: {type(e).__name__}") from e
