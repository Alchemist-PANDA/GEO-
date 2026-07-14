import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session

from geo_audit_agent.agents.unified_competitor_agent import run_competitor_scan
from geo_audit_agent.api.auth import get_current_user
from geo_audit_agent.db.models import Brand
from geo_audit_agent.db.session import get_async_session

router = APIRouter()
logger = logging.getLogger(__name__)


class CompetitorScanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand_id: uuid.UUID
    competitors: list[str] | None = None


class CompetitorScanResponse(BaseModel):
    brand: str
    category: str
    city: str
    brand_scores: dict
    competitors: list
    summary: dict


@router.post("/competitors/scan", response_model=CompetitorScanResponse)
async def scan_competitors(
    payload: CompetitorScanRequest,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session),
):
    try:
        brand = session.get(Brand, payload.brand_id)
        if not brand or str(brand.user_id) != user_id:
            raise HTTPException(status_code=404, detail="Brand not found")
        result = run_competitor_scan(
            brand_name=brand.name,
            category=brand.category,
            city=brand.city,
            competitors=payload.competitors,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Competitor scan failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Competitor scan failed") from e
