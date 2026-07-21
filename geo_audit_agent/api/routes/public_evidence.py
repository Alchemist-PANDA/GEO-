"""Authenticated public-evidence endpoint used by the SME audit workflow."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session

from geo_audit_agent.api.auth import get_current_user
from geo_audit_agent.db.models import Brand
from geo_audit_agent.db.session import get_async_session
from geo_audit_agent.services.public_evidence import crawl_public_evidence

router = APIRouter()


class PublicEvidenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    brand_id: uuid.UUID
    website_url: str | None = None


@router.post("/evidence/public")
async def collect_public_evidence(
    payload: PublicEvidenceRequest,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session),
):
    brand = session.get(Brand, payload.brand_id)
    if not brand or str(brand.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Brand not found")
    url = payload.website_url or brand.website_url
    if not url:
        raise HTTPException(status_code=422, detail="A website URL is required")
    try:
        return crawl_public_evidence(url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Public website evidence could not be collected") from exc
