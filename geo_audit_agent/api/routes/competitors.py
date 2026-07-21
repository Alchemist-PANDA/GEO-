import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session

from geo_audit_agent.agents.unified_competitor_agent import run_competitor_scan
from geo_audit_agent.api.auth import get_current_user
from geo_audit_agent.db.models import Brand
from geo_audit_agent.db.session import get_async_session
from geo_audit_agent.services.public_evidence import crawl_public_evidence

router = APIRouter()
logger = logging.getLogger(__name__)


class CompetitorScanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand_id: uuid.UUID
    competitors: list[str] | None = None
    competitor_websites: dict[str, str] | None = None


class CompetitorScanResponse(BaseModel):
    brand: str
    category: str
    city: str
    brand_scores: dict
    competitors: list
    summary: dict
    public_evidence: dict = Field(default_factory=dict)


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
        evidence: dict[str, dict] = {}
        urls = {brand.name: brand.website_url} if brand.website_url else {}
        urls.update(payload.competitor_websites or {})
        for entity, url in urls.items():
            if not url:
                continue
            try:
                evidence[entity] = crawl_public_evidence(url)
            except Exception as exc:
                logger.info("Public evidence unavailable for %s: %s", entity, type(exc).__name__)
                evidence[entity] = {"url": url, "status": "unavailable", "evidence_urls": []}
        result["public_evidence"] = evidence
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Competitor scan failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Competitor scan failed") from e
