# health.py
import logging

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from geo_audit_agent.db.session import get_async_session

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Simple API live health check."""
    return {"status": "healthy", "service": "BrandSight GEO API"}

@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(session: Session = Depends(get_async_session)):
    """Verifies internal database readiness."""
    try:
        session.exec(select(1)).one()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error("Readiness check failed on db query: %s", e)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unready", "database": "disconnected"},
        )
