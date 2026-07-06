import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from geo_audit_agent.agents.unified_competitor_agent import run_competitor_scan
from geo_audit_agent.api.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class CompetitorScanRequest(BaseModel):
    brand_name: str
    category: str
    city: str
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
):
    try:
        result = run_competitor_scan(
            brand_name=payload.brand_name,
            category=payload.category,
            city=payload.city,
            competitors=payload.competitors,
        )
        return result
    except Exception as e:
        logger.error("Competitor scan failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Competitor scan failed") from e
