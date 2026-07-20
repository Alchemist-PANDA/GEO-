# brands.py
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, func, select

from geo_audit_agent.api.auth import get_current_user
from geo_audit_agent.api.schemas import BrandCreate, BrandResponse
from geo_audit_agent.db.models import Audit, Brand
from geo_audit_agent.db.session import get_async_session

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/brands", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    payload: BrandCreate,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session)
):
    """Register a new brand under the current user's profile."""
    # Convert string uuid to UUID object
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authenticated identity") from None

    brand = Brand(
        name=payload.name,
        category=payload.category,
        city=payload.city,
        website_url=payload.website_url,
        user_id=user_uuid
    )

    try:
        session.add(brand)
        session.commit()
        session.refresh(brand)
        logger.info(f"Brand {brand.id} created for user {user_id}")
        return brand
    except Exception as e:
        session.rollback()
        logger.error("Failed to create brand: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register brand."
        ) from e

@router.get("/brands", response_model=list[BrandResponse])
async def list_brands(
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session)
):
    """Retrieve all registered brands belonging to the current user."""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authenticated identity") from None
    statement = select(Brand).where(Brand.user_id == user_uuid)
    brands = session.exec(statement).all()

    # Calculate audit counts for each brand
    response_brands = []
    for brand in brands:
        audit_count_stmt = select(func.count(1)).where(Audit.brand_id == brand.id)
        count = session.exec(audit_count_stmt).one()

        brand_data = brand.model_dump()
        brand_data["audit_count"] = count
        response_brands.append(BrandResponse(**brand_data))

    return response_brands

@router.get("/brands/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session)
):
    """Retrieve details for a specific brand."""
    brand = session.get(Brand, brand_id)
    if not brand or str(brand.user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )

    audit_count_stmt = select(func.count(1)).where(Audit.brand_id == brand.id)
    count = session.exec(audit_count_stmt).one()

    brand_data = brand.model_dump()
    brand_data["audit_count"] = count
    return BrandResponse(**brand_data)
