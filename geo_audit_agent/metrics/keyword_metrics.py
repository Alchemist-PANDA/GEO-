"""Evidence-backed keyword/query visibility metrics."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def calculate_keyword_metrics(rows: list[dict[str, Any]], keyword: str) -> dict[str, Any]:
    """Calculate a query-specific rate from successful live/cached observations."""
    query = keyword.strip().casefold()
    selected = [
        row for row in rows
        if str(row.get("keyword", row.get("query", ""))).strip().casefold() == query
        and row.get("mode") in {"live", "cached"}
        and not row.get("error")
    ]
    denominator = len(selected)
    numerator = sum(bool(row.get("mentioned")) for row in selected)
    return {
        "keyword": keyword,
        "value": numerator / denominator if denominator else None,
        "numerator": numerator,
        "denominator": denominator,
        "sample_size": denominator,
        "status": "measured" if denominator else "insufficient_evidence",
    }


def keyword_trend(rows: list[dict[str, Any]], keyword: str) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        period = str(row.get("run_date", row.get("created_at", "")))[:10]
        if period:
            grouped[period].append(row)
    periods = sorted(grouped)
    points = [calculate_keyword_metrics(grouped[period], keyword) for period in periods]
    return {
        "keyword": keyword,
        "periods": points,
        "status": "measured" if len([point for point in points if point["denominator"]]) >= 2 else "insufficient_evidence",
    }
