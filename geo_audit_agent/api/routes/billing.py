"""SME-friendly usage and sales-assisted billing endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from geo_audit_agent.api.auth import get_current_user
from geo_audit_agent.billing.plans import plan_limits
from geo_audit_agent.db.models import Audit, Brand, InvoiceRequest, UserProfile
from geo_audit_agent.db.session import get_async_session

router = APIRouter()


class InvoiceRequestCreate(BaseModel):
    tier: str = Field(..., pattern="^(starter|professional|business|enterprise)$")
    notes: str | None = Field(default=None, max_length=2000)


@router.get("/usage")
async def get_usage(
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session),
):
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authenticated identity") from None
    profile = session.get(UserProfile, user_uuid)
    plan = profile.tier if profile else "free"
    start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    brand_ids = session.exec(select(Brand.id).where(Brand.user_id == user_uuid)).all()
    audits = [
        audit for audit in session.exec(select(Audit).where(Audit.created_at >= start)).all()
        if audit.brand_id in set(brand_ids)
    ] if brand_ids else []
    limits = plan_limits(plan)
    return {
        "plan": plan,
        "current_month": start.strftime("%Y-%m"),
        "total_audits": len(audits),
        "total_tokens": sum(a.total_tokens for a in audits),
        "total_cost_usd": round(sum(a.total_cost_usd for a in audits), 6),
        "quota": limits["audits_per_month"],
        "quota_remaining": max(0, limits["audits_per_month"] - len(audits)),
        "brand_limit": limits["brands"],
        "white_label": limits["white_label"],
    }


@router.post("/billing/invoice-requests", status_code=status.HTTP_201_CREATED)
async def request_invoice(
    payload: InvoiceRequestCreate,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session),
):
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authenticated identity") from None
    profile = session.get(UserProfile, user_uuid)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    limits = plan_limits(payload.tier)
    request = InvoiceRequest(
        user_id=user_uuid,
        tier=payload.tier,
        amount=limits["price"],
        status="pending",
        notes=(payload.notes or "").strip() or None,
    )
    session.add(request)
    session.commit()
    session.refresh(request)
    return {"id": str(request.id), "tier": request.tier, "amount": request.amount, "status": request.status}
