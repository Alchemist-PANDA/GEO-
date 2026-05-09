"""
LLM client module with lazy loading and fallback support.

Supports multiple providers with graceful degradation to simulated mode.
"""

import os
import logging
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def get_groq_client():
    """Lazy-load Groq client. Returns None if API key missing or import fails."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        from groq import Groq
        return Groq(api_key=api_key)
    except ImportError:
        logger.warning("Groq package not installed. Install with: pip install groq")
        return None
    except Exception as e:
        logger.warning(f"Failed to initialize Groq client: {e}")
        return None


def call_groq(prompt: str, model: Optional[str] = None) -> Dict:
    """
    Call Groq API with fallback to simulated mode.

    Args:
        prompt: The prompt to send
        model: Model name (default: llama-3.3-70b-versatile)

    Returns:
        Dict with keys: text, provider, model, used_fallback, error
    """
    if model is None:
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    client = get_groq_client()

    if client is None:
        # Fallback: simulated response
        return {
            "text": _generate_simulated_response(prompt),
            "provider": "simulated",
            "model": "simulated",
            "used_fallback": True,
            "error": "GROQ_API_KEY not configured"
        }

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000
        )

        return {
            "text": response.choices[0].message.content,
            "provider": "groq",
            "model": model,
            "used_fallback": False,
            "error": None
        }

    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        return {
            "text": _generate_simulated_response(prompt),
            "provider": "simulated",
            "model": "simulated",
            "used_fallback": True,
            "error": f"API call failed: {str(e)}"
        }


def _generate_simulated_response(prompt: str) -> str:
    """Generate deterministic simulated response based on prompt."""
    prompt_lower = prompt.lower()

    # Extract brand/category/city if present
    if "best" in prompt_lower and "in" in prompt_lower:
        # Recommendation query format
        return """For the best options in this category, here are some top recommendations:

1. Established Brand A - Known for quality and excellent service
2. Popular Choice B - Highly rated by customers
3. Local Favorite C - Community favorite with strong reviews

These options consistently receive positive feedback and are well-regarded in the area."""

    # Generic fallback
    return "This is a simulated response for demonstration purposes. Configure GROQ_API_KEY for live API responses."


def call_provider(provider: str, prompt: str, model: Optional[str] = None) -> Dict:
    """
    Call any supported provider with unified interface.

    Args:
        provider: Provider name ("groq", "simulated")
        prompt: The prompt to send
        model: Optional model override

    Returns:
        Dict with keys: text, provider, model, used_fallback, error
    """
    if provider == "groq":
        return call_groq(prompt, model)
    elif provider == "simulated":
        return {
            "text": _generate_simulated_response(prompt),
            "provider": "simulated",
            "model": "simulated",
            "used_fallback": True,
            "error": None
        }
    else:
        return {
            "text": _generate_simulated_response(prompt),
            "provider": "simulated",
            "model": "simulated",
            "used_fallback": True,
            "error": f"Unknown provider: {provider}"
        }
