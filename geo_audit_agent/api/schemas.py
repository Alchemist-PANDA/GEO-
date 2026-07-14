import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

# ── Request Schemas ──

class BrandCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["Burger Hub"])
    category: str = Field(..., min_length=1, max_length=100, examples=["restaurant"])
    city: str = Field(..., min_length=1, max_length=100, examples=["Islamabad"])
    website_url: str | None = Field(None, max_length=500)

    @field_validator("name", "category", "city")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class AuditCreate(BaseModel):
    brand_id: uuid.UUID
    tier: str = Field(default="balanced", pattern="^(express|balanced|deep)$")


class CompetitorAnalysisRequest(BaseModel):
    brand_name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    limit: int = Field(default=5, ge=1, le=20)


class RemediationRequest(BaseModel):
    brand_name: str = Field(...)
    competitor_name: str = Field(...)
    strategy_text: str = Field(...)


class CompetitorFeedbackRequest(BaseModel):
    competitor_id: str = Field(...)
    is_helpful: bool = Field(...)
    comment: str | None = Field(None, max_length=1000)


class FeedbackCreate(BaseModel):
    feedback_type: str = Field(..., pattern="^(thumbs_up|thumbs_down|nps)$")
    nps_score: int | None = Field(None, ge=0, le=10)
    comment: str | None = Field(None, max_length=1000)

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
    website_url: str | None
    created_at: datetime
    audit_count: int = 0


class AuditResponse(BaseModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    tier: str
    status: str
    is_cited: bool
    confidence_score: float
    sentiment: str | None
    gaps: list[dict[str, Any]]
    remediations: dict[str, Any]
    competitors: list[str]
    predicted_geo_score: float | None
    total_cost_usd: float
    started_at: datetime | None
    completed_at: datetime | None
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
    data: dict[str, Any]


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
