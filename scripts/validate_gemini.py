"""Quota-safe Gemini integration validation for BrandSight GEO.

This intentionally validates the provider boundary and observation pipeline,
not statistical market visibility. It never prints or stores API keys.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from geo_audit_agent.testing.gemini_client import APIError, RateLimitError, generate_content_async


DEFAULT_PROMPTS = [
    "What should a customer look for when choosing a local marketing agency? Give a concise checklist.",
    "What are the best ways for a small business to improve its visibility in AI search results?",
    "How should a marketing agency explain AI-search visibility to a small-business owner?",
    "Compare the tradeoffs between local SEO and generative engine optimization for an SME.",
]


def _keys() -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    primary = os.getenv("GOOGLE_API_KEY")
    if primary:
        values.append(("GOOGLE_API_KEY", primary))
    for index in range(1, 8):
        value = os.getenv(f"GOOGLE_API_KEY_{index}")
        if value and value != primary:
            values.append((f"GOOGLE_API_KEY_{index}", value))
    return values


def _is_quota_error(error: Exception) -> bool:
    message = str(error).lower()
    return isinstance(error, RateLimitError) or any(
        marker in message for marker in ("429", "quota", "resource exhausted", "rate limit")
    )


async def run(args: argparse.Namespace) -> dict[str, object]:
    keys = _keys()
    if not keys:
        raise SystemExit("No Gemini key configured. Set GOOGLE_API_KEY in a local .env or shell environment.")
    max_requests = min(args.max_requests, int(os.getenv("GEMINI_VALIDATION_MAX_REQUESTS", "4")))
    prompts = args.prompt or DEFAULT_PROMPTS
    prompts = prompts[:max_requests]
    model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    results: list[dict[str, object]] = []
    request_count = 0
    key_index = 0

    for prompt_index, prompt in enumerate(prompts, start=1):
        while True:
            key_name, key = keys[key_index]
            request_count += 1
            try:
                text, raw = await generate_content_async(
                    prompt,
                    model=model,
                    api_key=key,
                    max_output_tokens=args.max_output_tokens,
                )
                usage = raw.get("usageMetadata", {}) if isinstance(raw, dict) else {}
                item: dict[str, object] = {
                    "prompt_index": prompt_index,
                    "key_slot": key_name,
                    "model": model,
                    "status": "passed" if text.strip() else "failed_empty_response",
                    "response_chars": len(text),
                    "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "input_tokens": usage.get("promptTokenCount"),
                    "output_tokens": usage.get("candidatesTokenCount"),
                }
                if args.save_responses:
                    item["response"] = text
                results.append(item)
                break
            except (RateLimitError, APIError) as error:
                results.append({
                    "prompt_index": prompt_index,
                    "key_slot": key_name,
                    "model": model,
                    "status": "quota_or_error",
                    "error_type": type(error).__name__,
                })
                if not args.allow_key_failover or not _is_quota_error(error) or key_index + 1 >= len(keys):
                    break
                key_index += 1
                # One controlled retry on the next cold key; never round-robin.
                continue
        if request_count >= max_requests:
            break

    return {
        "validation": "gemini_provider_boundary",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "request_budget": max_requests,
        "requests_attempted": request_count,
        "keys_configured": len(keys),
        "failover_enabled": args.allow_key_failover,
        "passed": sum(1 for item in results if item["status"] == "passed"),
        "results": results,
        "interpretation": "Integration evidence only; not a statistically reliable GEO visibility score.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", action="append", help="One prompt; repeat for a small fixed corpus.")
    parser.add_argument("--max-requests", type=int, default=4)
    parser.add_argument("--max-output-tokens", type=int, default=int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "512")))
    parser.add_argument("--allow-key-failover", action="store_true", help="Use the next configured key only after quota errors.")
    parser.add_argument("--save-responses", action="store_true", help="Include response text in the local report; review for PII before sharing.")
    parser.add_argument("--output", type=Path, default=Path("validation_artifacts/gemini/validation.json"))
    args = parser.parse_args()
    report = asyncio.run(run(args))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("model", "request_budget", "requests_attempted", "keys_configured", "passed")}, indent=2))


if __name__ == "__main__":
    main()
