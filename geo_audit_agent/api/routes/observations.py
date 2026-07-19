"""Evidence and metric endpoints for the SME audit workspace."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from geo_audit_agent.api.auth import get_current_user
from geo_audit_agent.db.models import Audit, Brand, ObservationEvidence
from geo_audit_agent.db.session import get_async_session
from geo_audit_agent.metrics.visibility_metrics import calculate_visibility_metrics

router = APIRouter()


def _owned_audit(audit_id: uuid.UUID, user_id: str, session: Session) -> Audit:
    audit = session.get(Audit, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    brand = session.get(Brand, audit.brand_id)
    if not brand or str(brand.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audit


@router.get("/audits/{audit_id}/evidence")
async def list_audit_evidence(
    audit_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session),
):
    """Return raw evidence and derived metrics for transparent reporting."""
    _owned_audit(audit_id, user_id, session)
    evidence = session.exec(
        select(ObservationEvidence)
        .where(ObservationEvidence.audit_id == audit_id)
        .order_by(ObservationEvidence.created_at)
    ).all()
    rows = [
        {
            "id": str(item.id),
            "provider": item.provider,
            "model": item.model,
            "prompt_id": item.prompt_id,
            "prompt_version": item.prompt_version,
            "mode": item.execution_mode,
            "raw_response": item.raw_response,
            "mentioned": item.mentioned,
            "recommended": item.recommendation,
            "position": item.position,
            "citation_urls": item.citation_urls,
            "sentiment": item.sentiment,
            "measurement_confidence": item.measurement_confidence,
            "latency_ms": item.latency_ms,
            "input_tokens": item.input_tokens,
            "output_tokens": item.output_tokens,
            "cost_usd": item.cost_usd,
            "cache_hit": item.cache_hit,
            "error": item.error_code,
            "created_at": item.created_at.isoformat(),
        }
        for item in evidence
    ]
    metrics = calculate_visibility_metrics(
        rows,
        expected_providers={row["provider"] for row in rows},
        expected_prompts={row["prompt_id"] for row in rows},
    )
    return {"audit_id": str(audit_id), "evidence": rows, "metrics": metrics.as_dict()}
