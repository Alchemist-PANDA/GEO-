"""Competitor comparison computed only from supplied provider observations."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from geo_audit_agent.metrics.visibility_metrics import calculate_visibility_metrics


def run_competitor_scan(
    brand_name: str,
    category: str,
    city: str,
    competitors: list[str] | None = None,
    observations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compare entities on like-for-like evidence; return unavailable without it."""
    requested = [brand_name, *(competitors or [])]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for observation in observations or []:
        entity = str(observation.get("entity", ""))
        if entity in requested:
            grouped[entity].append(observation)

    expected_providers = sorted({str(row.get("provider")) for row in observations or [] if row.get("provider")})
    expected_prompts = sorted({str(row.get("prompt_id")) for row in observations or [] if row.get("prompt_id")})
    comparisons: list[dict[str, Any]] = []
    for entity in requested:
        metrics = calculate_visibility_metrics(
            grouped[entity], expected_providers=expected_providers, expected_prompts=expected_prompts
        ).as_dict()
        comparisons.append({"entity": entity, "metrics": metrics, "sample_size": len(grouped[entity])})

    comparable = bool(observations) and all(item["sample_size"] > 0 for item in comparisons)
    return {
        "brand": brand_name,
        "category": category,
        "city": city,
        "brand_scores": comparisons[0]["metrics"],
        "competitors": comparisons[1:],
        "summary": {
            "status": "measured" if comparable else "insufficient_evidence",
            "total_competitors": len(competitors or []),
            "brand_rank": None,
            "top_opportunity": None,
            "reason": None if comparable else (
                "Collect like-for-like observations for the brand and every competitor before comparing them."
            ),
        },
    }
