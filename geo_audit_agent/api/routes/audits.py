import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, desc

from geo_audit_agent.api.auth import get_current_user
from geo_audit_agent.api.schemas import AuditCreate, AuditResponse, AuditSummary
from geo_audit_agent.db.models import Audit, Brand, AuditStatus
from geo_audit_agent.db.session import get_async_session
from geo_audit_agent.services.cost_tracker import TokenCostTracker
from geo_audit_agent.workers.tasks import run_audit_task

router = APIRouter()
logger = logging.getLogger(__name__)
cost_tracker = TokenCostTracker()


@router.post("/audits", response_model=AuditResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_audit(
    payload: AuditCreate,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session),
):
    brand = session.get(Brand, payload.brand_id)
    if not brand or str(brand.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Brand not found")

    if cost_tracker.is_budget_exceeded(user_id):
        raise HTTPException(status_code=402, detail="Monthly budget exceeded")

    audit = Audit(
        brand_id=payload.brand_id,
        tier=payload.tier,
        status=AuditStatus.PENDING,
    )
    session.add(audit)
    session.commit()
    session.refresh(audit)

    run_audit_task.delay(str(audit.id), user_id)
    logger.info(f"Audit {audit.id} queued for brand {brand.name}")

    return audit


@router.get("/audits/{audit_id}", response_model=AuditResponse)
async def get_audit(
    audit_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session),
):
    audit = session.get(Audit, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    brand = session.get(Brand, audit.brand_id)
    if not brand or str(brand.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Audit not found")

    return audit


@router.get("/brands/{brand_id}/audits", response_model=list[AuditSummary])
async def list_brand_audits(
    brand_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session),
):
    brand = session.get(Brand, brand_id)
    if not brand or str(brand.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Brand not found")

    statement = (
        select(Audit)
        .where(Audit.brand_id == brand_id)
        .order_by(desc(Audit.created_at))
        .limit(50)
    )
    audits = session.exec(statement).all()
    return audits
