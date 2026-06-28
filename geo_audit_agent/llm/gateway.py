"""Unified LLM gateway. All model access goes through here so provider,
cost accounting, and mock-mode live in exactly one place."""
from __future__ import annotations
import json, os, logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    provider: str = "mock"


def _mock(prompt: str, tag: str) -> LLMResult:
    return LLMResult(text=json.dumps({"mock": True, "tag": tag,
        "echo": prompt[:120]}), provider="mock")


def claude(system: str, user: str, *, model: str = "claude-opus-4-8",
           max_tokens: int = 4096, force_json: bool = False) -> LLMResult:
    """Reasoning calls (Inspector, Improvement Proposer). Current Anthropic
    SDK shape: adaptive thinking, streaming with get_final_message()."""
    if os.getenv("FORCE_MOCK") == "true" or not os.getenv("ANTHROPIC_API_KEY"):
        return _mock(user, "claude")
    import anthropic
    client = anthropic.Anthropic()
    sys_prompt = system + ("\n\nRespond with ONLY valid JSON." if force_json else "")
    try:
        # Streaming avoids request-timeout on long reasoning; adaptive thinking
        # is the current default for 4.6+ models (budget_tokens is rejected).
        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            system=sys_prompt,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            msg = stream.get_final_message()
        text = "".join(b.text for b in msg.content if b.type == "text")
        usage = getattr(msg, "usage", None)
        return LLMResult(
            text=text,
            input_tokens=getattr(usage, "input_tokens", 0) if usage else 0,
            output_tokens=getattr(usage, "output_tokens", 0) if usage else 0,
            cost_usd=_price("claude-opus", usage),
            provider="anthropic",
        )
    except Exception as e:
        logger.warning("Claude gateway failed, returning mock: %s", e)
        return _mock(user, "claude-error")


def router(prompt: str, tier: str = "balanced", correlation_id: str = "") -> LLMResult:
    """Audit/competitor calls — delegate to the EXISTING Gemini router."""
    if os.getenv("FORCE_MOCK") == "true":
        return _mock(prompt, "router")
    from geo_audit_agent.services.llm_router import query_provider
    r = query_provider(prompt=prompt, tier=tier, correlation_id=correlation_id)
    return LLMResult(text=r.text, output_tokens=r.total_tokens,
                     cost_usd=r.cost_usd, provider=r.provider)


def parse_json(text: str) -> dict:
    """Tolerant JSON extraction from model output."""
    try:
        s, e = text.find("{"), text.rfind("}") + 1
        return json.loads(text[s:e]) if s != -1 and e else {}
    except Exception:
        return {}


_PRICES = {"claude-opus": (5.0, 25.0)}  # $/1M in, $/1M out (Opus 4.8)

def _price(key: str, usage) -> float:
    if not usage:
        return 0.0
    pin, pout = _PRICES.get(key, (0.0, 0.0))
    return (getattr(usage, "input_tokens", 0) / 1e6) * pin + \
           (getattr(usage, "output_tokens", 0) / 1e6) * pout
