"""Canonical, JSON-friendly audit context shared by every Streamlit workspace."""
from __future__ import annotations

import csv
import io
import json
import uuid
from collections.abc import MutableMapping
from typing import Any


def build_audit_context(
    audit: dict[str, Any], audit_input: dict[str, Any], *, audit_id: str | None = None,
) -> dict[str, Any]:
    results = list(audit.get("results") or [])
    summary = dict(audit.get("summary") or {})
    source = summary.get("data_source", "unavailable")
    gaps: list[dict[str, Any]] = []
    for result in results:
        if result.get("mode") == "failed":
            continue
        if result.get("mentioned") is False:
            provider = result.get("provider") or result.get("model") or "provider"
            gaps.append({
                "id": f"missing-mention-{provider}",
                "gap_type": "content authority",
                "severity": "High",
                "description": f"Brand was not mentioned in the {provider} recommendation observation.",
                "provider": provider,
                "evidence": result.get("evidence", "Brand not mentioned"),
                "execution_mode": result.get("mode"),
            })

    visibility = summary.get("visibility_score")
    score = round(float(visibility) * 100) if visibility is not None else None
    context = {
        "id": audit_id or str(uuid.uuid4()),
        "brand_name": audit_input.get("brand", ""),
        "category": audit_input.get("category", ""),
        "city": audit_input.get("city", ""),
        "run_at": audit_input.get("run_at"),
        "requested_mode": audit_input.get("requested_mode", "fixture"),
        "data_source": source,
        "results": results,
        "summary": summary,
        "public_evidence": dict(audit.get("public_evidence") or {}),
        "gaps": gaps,
        "report": {
            "geo_score": score,
            "data_source": source,
            "models_requested": summary.get("models_requested", len(results)),
            "models_tested": summary.get("models_tested", 0),
        },
        "is_cited": any(bool(row.get("citation_urls")) for row in results if row.get("mode") != "fixture"),
        "sentiment": "unscored",
    }
    return context


def activate_audit_context(state: MutableMapping[str, Any], context: dict[str, Any], *, max_history: int = 10) -> None:
    """Publish one canonical record under legacy keys until all pages migrate."""
    state["active_audit"] = context
    state["active_audit_id"] = context["id"]
    state["audit_result"] = context
    state["audit_results"] = context
    state["brand_name"] = context["brand_name"]
    state["category"] = context["category"]
    state["city"] = context["city"]
    state["verified_audit"] = {"results": context["results"], "summary": context["summary"]}
    state["verified_audit_input"] = {
        "brand": context["brand_name"],
        "category": context["category"],
        "city": context["city"],
        "run_at": context["run_at"],
        "requested_mode": context["requested_mode"],
    }
    history = [item for item in list(state.get("audit_history") or []) if item.get("id") != context["id"]]
    state["audit_history"] = [context, *history][:max_history]


def audit_json(context: dict[str, Any]) -> str:
    return json.dumps(context, indent=2, default=str)


def audit_csv(context: dict[str, Any]) -> str:
    output = io.StringIO()
    fields = ["model", "provider", "mode", "mentioned", "position", "latency_ms", "evidence"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(context.get("results") or [])
    return output.getvalue()


def audit_markdown(context: dict[str, Any]) -> str:
    report = context.get("report") or {}
    lines = [
        f"# BrandSight GEO audit — {context.get('brand_name', 'Unknown brand')}",
        "",
        f"- Market: {context.get('city') or 'Not provided'}",
        f"- Category: {context.get('category') or 'Not provided'}",
        f"- Run at: {context.get('run_at') or 'Unknown'}",
        f"- Data source: {context.get('data_source', 'unavailable').upper()}",
        f"- GEO score: {report.get('geo_score') if report.get('geo_score') is not None else 'Insufficient evidence'}",
        "",
        "## Provider observations",
    ]
    for row in context.get("results") or []:
        lines.extend([
            "",
            f"### {row.get('model', row.get('provider', 'Provider'))}",
            f"- Mode: {row.get('mode', 'failed')}",
            f"- Mentioned: {row.get('mentioned')}",
            f"- Evidence: {row.get('evidence', 'Unavailable')}",
        ])
    if context.get("gaps"):
        lines.extend(["", "## Identified gaps"])
        lines.extend(f"- {gap['description']}" for gap in context["gaps"])
    return "\n".join(lines) + "\n"
