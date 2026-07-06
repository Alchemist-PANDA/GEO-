"""Unified LLM gateway. All model access goes through here so provider,
cost accounting, and mock-mode live in exactly one place."""
from __future__ import annotations
import json
import os
import logging
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
    if os.getenv("FORCE_MOCK") == "true" or not os.getenv("ANTHROPIC_API_KEY"):
        return _mock(user, "claude")
    import anthropic
    client = anthropic.Anthropic()
    sys_prompt = system + ("\n\nRespond with ONLY valid JSON." if force_json else "")
    try:
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
        result = LLMResult(
            text=text,
            input_tokens=getattr(usage, "input_tokens", 0) if usage else 0,
            output_tokens=getattr(usage, "output_tokens", 0) if usage else 0,
            cost_usd=_price("claude-opus", usage),
            provider="anthropic",
        )
        _record_metrics(result, model, cache_hit=False)
        return result
    except Exception as e:
        logger.warning("Claude gateway failed, returning mock: %s", e)
        return _mock(user, "claude-error")


def router(prompt: str, tier: str = "balanced", correlation_id: str = "") -> LLMResult:
    if os.getenv("FORCE_MOCK") == "true":
        return _mock(prompt, "router")
    from geo_audit_agent.services.llm_router import query_provider
    r = query_provider(prompt=prompt, tier=tier, correlation_id=correlation_id)
    return LLMResult(text=r.text, output_tokens=r.total_tokens,
                     cost_usd=r.cost_usd, provider=r.provider)


def parse_json(text: str) -> dict:
    try:
        s, e = text.find("{"), text.rfind("}") + 1
        return json.loads(text[s:e]) if s != -1 and e else {}
    except Exception:
        return {}


def _record_metrics(result: LLMResult, model: str, cache_hit: bool = False):
    try:
        from geo_audit_agent.observability.metrics import LLM_REQUESTS, LLM_TOKENS, LLM_COST
        LLM_REQUESTS.labels(provider=result.provider, model=model, cache_hit=str(cache_hit)).inc()
        if result.input_tokens:
            LLM_TOKENS.labels(provider=result.provider, direction="input").inc(result.input_tokens)
        if result.output_tokens:
            LLM_TOKENS.labels(provider=result.provider, direction="output").inc(result.output_tokens)
        if result.cost_usd:
            LLM_COST.labels(provider=result.provider, tier="standard").inc(result.cost_usd)
    except Exception:
        pass


_PRICES = {"claude-opus": (5.0, 25.0)}

def _price(key: str, usage) -> float:
    if not usage:
        return 0.0
    pin, pout = _PRICES.get(key, (0.0, 0.0))
    return (getattr(usage, "input_tokens", 0) / 1e6) * pin + \
           (getattr(usage, "output_tokens", 0) / 1e6) * pout
