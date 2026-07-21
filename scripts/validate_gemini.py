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
from typing import Any

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

from geo_audit_agent.testing.gemini_client import APIError, RateLimitError  # noqa: E402

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


def _allowed_key_slots() -> set[str] | None:
    configured = os.getenv("GEMINI_KEY_SLOTS")
    if not configured:
        return None
    return {slot.strip() for slot in configured.split(",") if slot.strip()}


def _keys() -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    allowed_slots = _allowed_key_slots()
    primary = os.getenv("GOOGLE_API_KEY")
    if primary and (allowed_slots is None or "GOOGLE_API_KEY" in allowed_slots):
        values.append(("GOOGLE_API_KEY", primary))
    for index in range(1, 8):
        key_name = f"GOOGLE_API_KEY_{index}"
        value = os.getenv(f"GOOGLE_API_KEY_{index}")
        if value and value != primary and (allowed_slots is None or key_name in allowed_slots):
            values.append((key_name, value))
    return values


def _is_quota_error(error: Exception) -> bool:
    message = str(error).lower()
    return isinstance(error, RateLimitError) or any(
        marker in message for marker in ("429", "quota", "resource exhausted", "rate limit")
    )


def _redact_error_message(message: str) -> str:
    redacted = message
    for _, key in _keys():
        if key:
            redacted = redacted.replace(key, "MASKED")
    redacted = re.sub(r"key=[^&\s]+", "key=MASKED", redacted)
    redacted = re.sub(r"api[_-]?key['\"]?\s*[:=]\s*['\"]?[^'\"\s,}]+", "api_key=MASKED", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"authorization['\"]?\s*[:=]\s*['\"]?[^'\"\s,}]+", "authorization=MASKED", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"AIza[0-9A-Za-z_\-]{20,}", "AIza...MASKED", redacted)
    redacted = re.sub(r"\bAQ\.[0-9A-Za-z_\-.]{12,}", "AQ...MASKED", redacted)
    return re.sub(r"\s+", " ", redacted).strip()


def _safe_error_details(error: Exception) -> dict[str, object]:
    """Return enough diagnostic detail to debug provider failures without secrets."""
    redacted = _redact_error_message(str(error))
    status_match = re.search(r"(?:status|HTTP|code)[^\d]*(\d{3})|^\s*(\d{3})\b", redacted, flags=re.IGNORECASE)
    http_status = None
    if status_match:
        status_value = status_match.group(1) or status_match.group(2)
        http_status = int(status_value) if status_value else None
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


def _usage_value(usage: Any, key: str) -> object:
    if usage is None:
        return None
    if isinstance(usage, dict):
        return usage.get(key)
    snake_key = re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()
    return getattr(usage, snake_key, None) or getattr(usage, key, None)


def _generate_content_sdk(prompt: str, *, model: str, api_key: str, max_output_tokens: int) -> tuple[str, dict[str, object]]:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise APIError("google-genai is not installed; install geo_audit_agent requirements before live validation") from exc

    try:
        with genai.Client(api_key=api_key) as client:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=max_output_tokens,
                ),
            )
            text = getattr(response, "text", "") or ""
            usage = getattr(response, "usage_metadata", None)
    except Exception as exc:
        raise APIError(f"Gemini SDK request failed: {_redact_error_message(str(exc))}") from exc

    return text, {
        "usageMetadata": {
            "promptTokenCount": _usage_value(usage, "promptTokenCount"),
            "candidatesTokenCount": _usage_value(usage, "candidatesTokenCount"),
        }
    }


async def generate_content_async(prompt: str, *, model: str, api_key: str, max_output_tokens: int) -> tuple[str, dict[str, object]]:
    return await asyncio.to_thread(
        _generate_content_sdk,
        prompt,
        model=model,
        api_key=api_key,
        max_output_tokens=max_output_tokens,
    )


def _load_cases(args: argparse.Namespace) -> list[dict[str, object]]:
    if args.corpus:
        data = json.loads(args.corpus.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise SystemExit("Corpus must be a JSON array of case objects.")
        cases: list[dict[str, object]] = []
        for index, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                raise SystemExit(f"Corpus item {index} must be an object.")
            prompt = item.get("prompt")
            if not isinstance(prompt, str) or not prompt.strip():
                raise SystemExit(f"Corpus item {index} is missing a non-empty prompt.")
            case = dict(item)
            case.setdefault("prompt_id", f"prompt_{index}")
            case["prompt"] = prompt
            cases.append(case)
        return cases

    prompts = args.prompt or DEFAULT_PROMPTS
    return [
        {
            "prompt_index": index,
            "prompt_id": f"prompt_{index}",
            "prompt": prompt,
        }
        for index, prompt in enumerate(prompts, start=1)
    ]


def _case_metadata(case: dict[str, object], prompt_index: int) -> dict[str, object]:
    metadata: dict[str, object] = {
        "prompt_index": prompt_index,
        "prompt_id": case.get("prompt_id", f"prompt_{prompt_index}"),
    }
    for field in ("business_name", "category", "city_or_market", "website", "public_info"):
        value = case.get(field)
        if value:
            metadata[field] = value
    return metadata


async def run(args: argparse.Namespace) -> dict[str, object]:
    keys = _keys()
    if not keys:
        raise SystemExit("No Gemini key configured. Set GOOGLE_API_KEY in a local .env or shell environment.")
    max_requests = min(args.max_requests, int(os.getenv("GEMINI_VALIDATION_MAX_REQUESTS", "4")))
    cases = _load_cases(args)
    cases = cases[:max_requests]
    model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    results: list[dict[str, object]] = []
    request_count = 0
    key_index = 0

    for prompt_index, case in enumerate(cases, start=1):
        prompt = str(case["prompt"])
        metadata = _case_metadata(case, prompt_index)
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
                    **metadata,
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
                    **metadata,
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
        "key_slots_configured": [key_name for key_name, _ in keys],
        "failover_enabled": args.allow_key_failover,
        "passed": sum(1 for item in results if item["status"] == "passed"),
        "results": results,
        "interpretation": "Integration evidence only; not a statistically reliable GEO visibility score.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, help="JSON array of case-study prompt objects.")
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
