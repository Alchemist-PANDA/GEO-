import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


# ── Request Schemas ──

class BrandCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["Burger Hub"])
    category: str = Field(..., min_length=1, max_length=100, examples=["restaurant"])
    city: str = Field(..., min_length=1, max_length=100, examples=["Islamabad"])
    website_url: Optional[str] = Field(None, max_length=500)

    @field_validator("name", "category", "city")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class AuditCreate(BaseModel):
    brand_id: uuid.UUID
    tier: str = Field(default="balanced", pattern="^(express|balanced|deep)$")


class FeedbackCreate(BaseModel):
    feedback_type: str = Field(..., pattern="^(thumbs_up|thumbs_down|nps)$")
    nps_score: Optional[int] = Field(None, ge=0, le=10)
    comment: Optional[str] = Field(None, max_length=1000)

    @field_validator("nps_score")
    @classmethod
    def validate_nps(cls, v, info):
        if info.data.get("feedback_type") == "nps" and v is None:
            raise ValueError("nps_score required when feedback_type is 'nps'")
        return v


# ── Response Schemas ──

class BrandResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: str
    city: str
    website_url: Optional[str]
    created_at: datetime
    audit_count: int = 0


class AuditResponse(BaseModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    tier: str
    status: str
    is_cited: bool
    confidence_score: float
    sentiment: Optional[str]
    gaps: List[Dict[str, Any]]
    remediations: Dict[str, Any]
    competitors: List[str]
    predicted_geo_score: Optional[float]
    total_cost_usd: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


class AuditSummary(BaseModel):
    id: uuid.UUID
    tier: str
    status: str
    is_cited: bool
    confidence_score: float
    created_at: datetime


class UsageResponse(BaseModel):
    current_month: str
    total_audits: int
    total_tokens: int
    total_cost_usd: float
    quota_remaining: int
    budget_limit_usd: float


class SSEEvent(BaseModel):
    event: str  # status_update, step_complete, audit_complete, error
    data: Dict[str, Any]


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
