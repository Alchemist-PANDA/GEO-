# llm_router.py
import os
import logging
from google import genai
from google.genai import types
from geo_audit_agent.llm_client import call_proxy_llm

logger = logging.getLogger(__name__)

class LLMProviderResponse:
    def __init__(self, text: str, total_tokens: int = 200, cost_usd: float = 0.0001, provider: str = "fallback"):
        self.text = text
        self.total_tokens = total_tokens
        self.cost_usd = cost_usd
        self.provider = provider

def query_provider(prompt: str, tier: str = "balanced", correlation_id: str = "") -> LLMProviderResponse:
    """Routes prompt queries to the appropriate LLM provider depending on the tier constraint."""
    api_key = os.getenv("GOOGLE_API_KEY")
    messages = [{"role": "user", "content": prompt}]
    
    if api_key:
        try:
            logger.info(f"Routing to Google Gemini API for {tier} tier (Correlation ID: {correlation_id})")
            client = genai.Client(api_key=api_key)
            
            # Map tier constraints to target models
            model_name = "gemini-2.0-flash-lite"
            if tier == "deep":
                model_name = "gemini-2.0-flash"
                
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
            logger.warning(f"Google GenAI routing failed, falling back to legacy proxy: {e}")
            
    # Legacy proxy fallback
    try:
        logger.info(f"Routing to fallback legacy proxy client (Correlation ID: {correlation_id})")
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
        logger.error(f"Fallback proxy call failed: {e}")
        # Deterministic simulation fallback to prevent pipeline crashes
        simulated_text = f"Simulated visibility response for prompt: {prompt[:50]}..."
        return LLMProviderResponse(
            text=simulated_text,
            total_tokens=10,
            cost_usd=0.0,
            provider="simulation_fallback"
        )
