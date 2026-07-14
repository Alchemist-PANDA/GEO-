# feedback_route.py
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from geo_audit_agent.api.auth import get_current_user
from geo_audit_agent.api.schemas import FeedbackCreate
from geo_audit_agent.db.models import Audit, AuditFeedback, Brand
from geo_audit_agent.db.session import get_async_session
from geo_audit_agent.services.feedback import FeedbackPersistenceManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize feedback persistence manager
feedback_manager = FeedbackPersistenceManager()

@router.post("/audits/{audit_id}/feedback", status_code=status.HTTP_201_CREATED)
async def submit_audit_feedback(
    audit_id: uuid.UUID,
    payload: FeedbackCreate,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session)
):
    """Submit user rating feedback (thumbs_up/thumbs_down/NPS score) for a finished audit."""
    audit = session.get(Audit, audit_id)
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit not found"
        )

    brand = session.get(Brand, audit.brand_id)
    if not brand or str(brand.user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this audit record."
        )

    # Scale NPS or thumbs rating values
    nps_score = payload.nps_score if payload.nps_score is not None else (10 if payload.feedback_type == "thumbs_up" else 0)
    comment = payload.comment or ""

    feedback = AuditFeedback(
        audit_id=audit.id,
        user_id=uuid.UUID(user_id),
        feedback_type=payload.feedback_type,
        nps_score=nps_score,
        comment=comment,
    )
    try:
        session.add(feedback)
        session.commit()
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record feedback."
        ) from exc

    # Redis is a secondary analytics sink. Durable database persistence above
    # remains the source of truth when Redis is unavailable.
    if not feedback_manager.submit_feedback(
        run_id=str(audit_id), brand_name=brand.name, score_nps=nps_score,
        rating_verdict=payload.feedback_type, user_comment=comment,
    ):
        logger.warning("Feedback analytics sink unavailable for audit %s", audit_id)

    return {"message": "Feedback submitted successfully."}
