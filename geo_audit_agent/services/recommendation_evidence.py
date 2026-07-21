"""Require recommendations to carry traceable evidence or an explicit caveat."""

from __future__ import annotations

from typing import Any


def attach_evidence(recommendations: list[dict[str, Any]], evidence: dict[str, Any]) -> list[dict[str, Any]]:
    urls = list(evidence.get("evidence_urls") or [])
    result = []
    for recommendation in recommendations:
        item = dict(recommendation)
        item["evidence_urls"] = urls[:5]
        item["evidence_status"] = "supported" if urls else "unverified"
        if not urls:
            item["caveat"] = "No public source was collected; verify this recommendation before client delivery."
        result.append(item)
    return result
