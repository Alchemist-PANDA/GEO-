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
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Support `python scripts/validate_gemini.py` from a fresh checkout without
# requiring the package to be installed first.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency preflight handles this.
    load_dotenv = None
else:
    load_dotenv(PROJECT_ROOT / ".env")

from geo_audit_agent.testing.gemini_client import APIError, RateLimitError, generate_content_async


DEFAULT_PROMPTS = [
    (
        "A local dental clinic wants more high-intent patients from AI search. "
        "What should it improve first across website content, local proof, and review signals?"
    ),
    (
        "A B2B accounting firm serving SMEs wants to be recommended by AI assistants. "
        "Give a concise GEO action plan that a small marketing agency could execute in 30 days."
    ),
    (
        "An independent HVAC company competes with franchises in one city. "
        "Which evidence, entities, and service-area pages help AI systems trust and mention it?"
    ),
    (
        "A boutique ecommerce brand sells organic skincare. "
        "Compare local SEO, traditional SEO, and generative engine optimization for this SME."
    ),
    (
        "A small legal practice wants to understand why AI search does not mention it. "
        "Explain the diagnostic questions a marketing agency should ask before recommending fixes."
    ),
    (
        "A restaurant group with three locations wants better AI-search visibility. "
        "List the structured data, review, menu, and local citation improvements that matter most."
    ),
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


def _safe_error_details(error: Exception) -> dict[str, object]:
    """Return enough diagnostic detail to debug provider failures without secrets."""
    message = str(error)
    redacted = re.sub(r"key=[^&\s]+", "key=MASKED", message)
    redacted = re.sub(r"AIza[0-9A-Za-z_\-]{20,}", "AIza...MASKED", redacted)
    redacted = re.sub(r"\s+", " ", redacted).strip()
    status_match = re.search(r"(?:status|HTTP)\s+(\d{3})", redacted, flags=re.IGNORECASE)
    http_status = int(status_match.group(1)) if status_match else None
    lowered = redacted.lower()
    if _is_quota_error(error):
        category = "quota_or_rate_limit"
        key_action = "try_next_key"
    elif http_status in (401, 403) or any(marker in lowered for marker in ("api key not valid", "permission", "unauthorized", "forbidden")):
        category = "auth_or_permission"
        key_action = "check_key_or_project_access"
    elif http_status == 404 or any(marker in lowered for marker in ("not found", "not supported", "model")):
        category = "model_or_endpoint"
        key_action = "check_gemini_model"
    elif "network" in lowered:
        category = "network"
        key_action = "retry_later"
    else:
        category = "api_error"
        key_action = "inspect_error_summary"
    return {
        "error_category": category,
        "http_status": http_status,
        "error_summary": redacted[:320],
        "key_action": key_action,
    }


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
                error_details = _safe_error_details(error)
                results.append({
                    "prompt_index": prompt_index,
                    "key_slot": key_name,
                    "model": model,
                    "status": "quota_or_error",
                    "error_type": type(error).__name__,
                    **error_details,
                })
                if not args.allow_key_failover or error_details["key_action"] != "try_next_key" or key_index + 1 >= len(keys):
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
    parser.add_argument(
        "--no-key-failover",
        dest="allow_key_failover",
        action="store_false",
        default=True,
        help="Disable automatic backup-key use after a quota/rate-limit error.",
    )
    parser.add_argument("--save-responses", action="store_true", help="Include response text in the local report; review for PII before sharing.")
    parser.add_argument("--output", type=Path, default=Path("validation_artifacts/gemini/validation.json"))
    args = parser.parse_args()
    report = asyncio.run(run(args))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("model", "request_budget", "requests_attempted", "keys_configured", "passed")}, indent=2))


if __name__ == "__main__":
    main()
