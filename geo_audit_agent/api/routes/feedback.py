# feedback_route.py
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from geo_audit_agent.api.auth import get_current_user
from geo_audit_agent.api.schemas import FeedbackCreate
from geo_audit_agent.db.models import Audit, Brand
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
    
    success = feedback_manager.submit_feedback(
        run_id=str(audit_id),
        brand_name=brand.name,
        score_nps=nps_score,
        rating_verdict=payload.feedback_type,
        user_comment=comment
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record feedback."
        )
        
    # Trigger model retraining feature logging if nps score is positive
    if nps_score >= 8:
        try:
            from geo_audit_agent.services.retraining import ModelRetrainingPipeline
            retraining_pipeline = ModelRetrainingPipeline()
            features = retraining_pipeline.extract_features_from_feedback(
                {"score_nps": nps_score},
                {
                    "gaps": audit.gaps,
                    "competition_level": 0.5,  # Defaults
                    "brand_age_months": 12.0,
                    "backlink_count": 10.0,
                    "semantic_score": 0.8 if audit.is_cited else 0.2
                }
            )
            retraining_pipeline.append_new_training_data([features])
        except Exception as e:
            logger.warning(f"Failed to log retraining payload: {e}")
            
    return {"message": "Feedback submitted successfully."}
