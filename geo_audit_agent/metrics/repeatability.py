"""Repeated-run stability calculations for GEO observations."""

from __future__ import annotations

from typing import Any


def calculate_repeatability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [row for row in rows if row.get("mode") in {"live", "cached"} and not row.get("error")]
    if len(valid) < 2:
        return {"status": "insufficient_evidence", "sample_size": len(valid), "agreement_rate": None}
    values = [bool(row.get("mentioned")) for row in valid]
    agreements = sum(left == right for left, right in zip(values, values[1:], strict=False))
    comparisons = len(values) - 1
    return {
        "status": "measured",
        "sample_size": len(valid),
        "agreement_rate": agreements / comparisons,
        "comparisons": comparisons,
    }
