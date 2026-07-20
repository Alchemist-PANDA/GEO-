from __future__ import annotations

import os
import time
from dataclasses import dataclass

import requests

from .base import (
    ExecutionMode,
    ProviderAuthError,
    ProviderResult,
    ProviderUnavailableError,
)


def _price(provider: str, input_tokens: int, output_tokens: int) -> float:
    """Conservative configurable pricing; zero is allowed only in fixtures."""
    prices = {
        "google": (0.000075, 0.0003),
        "anthropic": (0.0008, 0.004),
        "openai": (0.0004, 0.0016),
        "perplexity": (0.001, 0.001),
    }
    input_price, output_price = prices.get(provider, (0.0, 0.0))
    return input_tokens / 1000 * input_price + output_tokens / 1000 * output_price


@dataclass
class FixtureAdapter:
    """Explicit deterministic demo data. This adapter is never selected implicitly."""

    name: str
    model: str
    response_text: str

    def query(self, prompt: str, *, prompt_id: str, prompt_version: str) -> ProviderResult:
        return ProviderResult(
            provider=self.name,
            model=self.model,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            text=self.response_text,
            mode=ExecutionMode.FIXTURE,
            metadata={"disclosure": "demo fixture; not a provider response"},
        )


@dataclass
class GeminiAdapter:
    name: str = "google"
    model: str = "gemini-2.0-flash-lite"

    def query(self, prompt: str, *, prompt_id: str, prompt_version: str) -> ProviderResult:
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ProviderUnavailableError("GOOGLE_API_KEY is not configured")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ProviderUnavailableError("google-genai is not installed") from exc
        started = time.perf_counter()
        try:
            response = genai.Client(api_key=key).models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=1000),
            )
        except Exception as exc:
            if any(marker in str(exc).lower() for marker in ("401", "403", "api key", "permission")):
                raise ProviderAuthError("Gemini rejected the configured credential") from exc
            raise ProviderUnavailableError(f"Gemini request failed: {type(exc).__name__}") from exc
        text = response.text or ""
        input_tokens = len(prompt.split())
        output_tokens = len(text.split())
        return ProviderResult(
            provider=self.name,
            model=self.model,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            text=text,
            mode=ExecutionMode.LIVE,
            latency_ms=int((time.perf_counter() - started) * 1000),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=_price(self.name, input_tokens, output_tokens),
        )


@dataclass
class AnthropicAdapter:
    name: str = "anthropic"
    model: str = "claude-haiku-4-5"

    def query(self, prompt: str, *, prompt_id: str, prompt_version: str) -> ProviderResult:
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ProviderUnavailableError("ANTHROPIC_API_KEY is not configured")
        try:
            import anthropic
        except ImportError as exc:
            raise ProviderUnavailableError("anthropic is not installed") from exc
        started = time.perf_counter()
        try:
            response = anthropic.Anthropic().messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            if any(marker in str(exc).lower() for marker in ("401", "403", "authentication", "api key")):
                raise ProviderAuthError("Anthropic rejected the configured credential") from exc
            raise ProviderUnavailableError(f"Anthropic request failed: {type(exc).__name__}") from exc
        text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", 0)
        output_tokens = getattr(usage, "output_tokens", 0)
        return ProviderResult(
            provider=self.name,
            model=self.model,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            text=text,
            mode=ExecutionMode.LIVE,
            latency_ms=int((time.perf_counter() - started) * 1000),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=_price(self.name, input_tokens, output_tokens),
        )


@dataclass
class OpenAICompatibleAdapter:
    name: str
    model: str
    api_key_env: str
    endpoint: str

    def query(self, prompt: str, *, prompt_id: str, prompt_version: str) -> ProviderResult:
        key = os.getenv(self.api_key_env)
        if not key:
            raise ProviderUnavailableError(f"{self.api_key_env} is not configured")
        started = time.perf_counter()
        try:
            response = requests.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": self.model, "temperature": 0, "messages": [{"role": "user", "content": prompt}]},
                timeout=(5, 45),
            )
        except requests.RequestException as exc:
            raise ProviderUnavailableError(f"{self.name} request failed: {type(exc).__name__}") from exc
        if response.status_code in (401, 403):
            raise ProviderAuthError(f"{self.name} rejected the configured credential")
        if response.status_code >= 400:
            raise ProviderUnavailableError(f"{self.name} returned HTTP {response.status_code}")
        try:
            payload = response.json()
            text = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderUnavailableError(f"{self.name} returned a malformed response") from exc
        usage = payload.get("usage", {})
        input_tokens = int(usage.get("prompt_tokens", 0))
        output_tokens = int(usage.get("completion_tokens", 0))
        return ProviderResult(
            provider=self.name,
            model=self.model,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            text=text,
            mode=ExecutionMode.LIVE,
            latency_ms=int((time.perf_counter() - started) * 1000),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=_price(self.name, input_tokens, output_tokens),
        )


def get_provider_adapter(provider: str):
    adapters = {
        "google": GeminiAdapter(),
        "anthropic": AnthropicAdapter(),
        "openai": OpenAICompatibleAdapter(
            name="openai",
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            api_key_env="OPENAI_API_KEY",
            endpoint="https://api.openai.com/v1/chat/completions",
        ),
        "perplexity": OpenAICompatibleAdapter(
            name="perplexity",
            model=os.getenv("PERPLEXITY_MODEL", "sonar"),
            api_key_env="PERPLEXITY_API_KEY",
            endpoint="https://api.perplexity.ai/chat/completions",
        ),
    }
    try:
        return adapters[provider]
    except KeyError as exc:
        raise ProviderUnavailableError(f"No live adapter exists for provider '{provider}'") from exc
