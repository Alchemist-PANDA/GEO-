from __future__ import annotations

import uuid

from geo_audit_agent.db.models import ObservationEvidence
from geo_audit_agent.metrics.observation import interpret_observation
from geo_audit_agent.providers import ProviderResult


def provider_result_to_evidence(
    result: ProviderResult,
    *,
    audit_id: uuid.UUID,
    brand: str,
    aliases: list[str] | None = None,
) -> ObservationEvidence:
    interpretation = interpret_observation(result.text, brand, aliases)
    return ObservationEvidence(
        audit_id=audit_id,
        provider=result.provider,
        model=result.model,
        prompt_id=result.prompt_id,
        prompt_version=result.prompt_version,
        execution_mode=result.mode.value,
        raw_response=result.text,
        mentioned=interpretation.mentioned,
        recommendation=(result.recommendation if result.recommendation is not None else interpretation.recommended),
        sentiment=result.sentiment or interpretation.sentiment,
        measurement_confidence=interpretation.confidence,
        position=result.position if result.position is not None else interpretation.position,
        citation_urls=result.citation_urls or interpretation.citation_urls,
        latency_ms=result.latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_usd=result.cost_usd,
        cache_hit=result.cache_hit,
        error_code=result.error_code,
    )


def evidence_as_metric_row(evidence: ObservationEvidence) -> dict:
    return {
        "provider": evidence.provider,
        "prompt_id": evidence.prompt_id,
        "mode": evidence.execution_mode,
        "mentioned": evidence.mentioned,
        "recommended": evidence.recommendation,
        "sentiment": evidence.sentiment,
        "measurement_confidence": evidence.measurement_confidence,
        "position": evidence.position,
        "citation_urls": evidence.citation_urls,
        "error": evidence.error_code,
    }


def report_to_evidence(report: dict, *, audit_id: uuid.UUID) -> ObservationEvidence:
    observation = report.get("observation") or {}
    return ObservationEvidence(
        audit_id=audit_id,
        provider=str(observation.get("provider", "unknown")),
        model=str(observation.get("model", "unknown")),
        prompt_id=str(observation.get("prompt_id", "category-recommendation")),
        prompt_version=str(observation.get("prompt_version", "1.0")),
        execution_mode=str(observation.get("execution_mode", "failed")),
        raw_response=str(observation.get("raw_response", "")),
        mentioned=bool(observation.get("mentioned")),
        recommendation=bool(observation.get("recommendation")),
        sentiment=observation.get("sentiment"),
        measurement_confidence=float(observation.get("measurement_confidence", 0.0)),
        position=observation.get("position"),
        citation_urls=list(observation.get("citation_urls") or []),
        latency_ms=int(observation.get("latency_ms", 0)),
        input_tokens=int(observation.get("input_tokens", 0)),
        output_tokens=int(observation.get("output_tokens", 0)),
        cost_usd=float(observation.get("cost_usd", 0.0)),
        cache_hit=bool(observation.get("cache_hit")),
        error_code=observation.get("error_code"),
    )
