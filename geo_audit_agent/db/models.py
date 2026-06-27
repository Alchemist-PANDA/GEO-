import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column as SAColumn, DateTime, text, Index, JSON, MetaData
import sqlmodel.main
JSONB = JSON

# Reset MetaData and registry to prevent Streamlit hot-reload duplicate class errors
SQLModel.metadata = MetaData()
if hasattr(sqlmodel.main, "default_registry"):
    sqlmodel.main.default_registry.dispose()
    sqlmodel.main.default_registry._class_registry.clear()


class AuditTier(str, Enum):
    EXPRESS = "express"
    BALANCED = "balanced"
    DEEP = "deep"


class AuditStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    VALIDATING = "validating"
    COMPLETE = "complete"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class FeedbackType(str, Enum):
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    NPS = "nps"


# ── Users (managed by Supabase Auth, mirrored for FK references) ──

class UserProfile(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "user_profiles"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        description="Maps to Supabase auth.users.id"
    )
    email: str = Field(index=True, max_length=255)
    display_name: Optional[str] = Field(default=None, max_length=100)
    plan_tier: str = Field(default="free", max_length=20)
    monthly_audit_quota: int = Field(default=10)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )

    brands: List["Brand"] = Relationship(back_populates="owner")


# ── Brands ──

class Brand(SQLModel, table=True):
    __tablename__ = "brands"
    __table_args__ = (
        Index("idx_brands_name_city", "name", "city"),
        {"extend_existing": True}
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user_profiles.id", index=True)
    name: str = Field(index=True, max_length=255)
    category: str = Field(max_length=100)
    city: str = Field(max_length=100)
    website_url: Optional[str] = Field(default=None, max_length=500)
    metadata_: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn("metadata", JSONB, server_default=text("'{}'"))
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )

    owner: UserProfile = Relationship(back_populates="brands")
    audits: List["Audit"] = Relationship(
        back_populates="brand",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


# ── Audits ──

class Audit(SQLModel, table=True):
    __tablename__ = "audits"
    __table_args__ = (
        Index("idx_audits_created_at", "created_at"),
        Index("idx_audits_status", "status"),
        {"extend_existing": True}
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_id: uuid.UUID = Field(foreign_key="brands.id", index=True)
    tier: str = Field(default=AuditTier.BALANCED, max_length=20)
    status: str = Field(default=AuditStatus.PENDING, max_length=20)

    # Core results
    llm_response: Optional[str] = Field(default=None)
    is_cited: bool = Field(default=False)
    confidence_score: float = Field(default=0.0)
    sentiment: Optional[str] = Field(default=None, max_length=20)

    # Structured results (JSONB)
    gaps: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn(JSONB, server_default=text("'{}'"))
    )
    planned_actions: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn(JSONB, server_default=text("'{}'"))
    )
    remediations: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn(JSONB, server_default=text("'{}'"))
    )
    competitors: List[str] = Field(
        default_factory=list,
        sa_column=SAColumn(JSONB, server_default=text("'[]'"))
    )
    anomalies: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn(JSONB, server_default=text("'{}'"))
    )
    report: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn(JSONB, server_default=text("'{}'"))
    )

    # Predictive scoring
    predicted_geo_score: Optional[float] = Field(default=None)

    # Cost tracking
    total_tokens: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)

    # Temporal workflow reference
    workflow_run_id: Optional[str] = Field(default=None, max_length=100)

    # Timestamps
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )

    brand: Brand = Relationship(back_populates="audits")
    feedback: List["AuditFeedback"] = Relationship(back_populates="audit")


# ── Feedback ──

class AuditFeedback(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "audit_feedback"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    audit_id: uuid.UUID = Field(foreign_key="audits.id", index=True)
    user_id: uuid.UUID = Field(foreign_key="user_profiles.id", index=True)
    feedback_type: str = Field(max_length=20)
    nps_score: Optional[int] = Field(default=None, ge=0, le=10)
    comment: Optional[str] = Field(default=None)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )

    audit: Audit = Relationship(back_populates="feedback")


# ── LLM Call Log (for cost tracking & debugging) ──

class LLMCallLog(SQLModel, table=True):
    __tablename__ = "llm_call_logs"
    __table_args__ = (
        Index("idx_llm_calls_audit_id", "audit_id"),
        Index("idx_llm_calls_created_at", "created_at"),
        {"extend_existing": True}
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    audit_id: uuid.UUID = Field(foreign_key="audits.id")
    user_id: uuid.UUID = Field(index=True)
    model: str = Field(max_length=100)
    provider: str = Field(max_length=50)
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    cost_usd: float = Field(default=0.0)
    latency_ms: int = Field(default=0)
    cache_hit: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )


# ── Guardrail Event Log ──

class GuardrailEvent(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "guardrail_events"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True)
    input_text: str
    classification: str = Field(max_length=20)  # safe / unsafe
    category: Optional[str] = Field(default=None, max_length=50)
    blocked: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )

# ── Competitor Intelligence ──

class Competitor(SQLModel, table=True):
    __tablename__ = "competitors"
    __table_args__ = (
        Index("idx_competitors_brand_id", "brand_id"),
        {"extend_existing": True}
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_id: uuid.UUID = Field(foreign_key="brands.id", index=True)
    name: str = Field(max_length=255)
    website: Optional[str] = Field(default=None, max_length=500)
    category: str = Field(default="", max_length=100)
    city: str = Field(default="", max_length=100)
    is_auto_discovered: bool = Field(default=True)
    added_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )


class CompetitorScan(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "competitor_scans"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    competitor_id: uuid.UUID = Field(foreign_key="competitors.id", index=True)
    scan_type: str = Field(default="weekly", max_length=20)
    status: str = Field(default="pending", max_length=20)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    crawl_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn("crawl_data", JSONB, server_default=text("'{}'"))
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )


class CompetitorScore(SQLModel, table=True):
    __tablename__ = "competitor_scores"
    __table_args__ = (
        Index("idx_scores_competitor_scan", "competitor_id", "scan_id"),
        {"extend_existing": True}
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    competitor_id: uuid.UUID = Field(foreign_key="competitors.id", index=True)
    scan_id: uuid.UUID = Field(foreign_key="competitor_scans.id", index=True)
    dimension: str = Field(max_length=50)  # authority, schema, content, reviews, entities, citations, brand
    score: float = Field(default=0.0)
    details: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn("details", JSONB, server_default=text("'{}'"))
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )


class CompetitorExplanation(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "competitor_explanations"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    competitor_id: uuid.UUID = Field(foreign_key="competitors.id", index=True)
    scan_id: uuid.UUID = Field(foreign_key="competitor_scans.id", index=True)
    explanation_type: str = Field(max_length=50)  # winning_factors, strategy, summary
    content: str = ""
    confidence: float = Field(default=0.0)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )


class Alert(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "alerts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user_profiles.id", index=True)
    competitor_id: Optional[uuid.UUID] = Field(default=None, foreign_key="competitors.id")
    alert_type: str = Field(max_length=50)  # visibility_change, competitor_update, new_opportunity
    severity: str = Field(default="info", max_length=20)  # critical, high, medium, info
    message: str = ""
    is_read: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )

class CompetitorFeedback(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "competitor_feedback"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user_profiles.id", index=True)
    competitor_id: uuid.UUID = Field(foreign_key="competitors.id", index=True)
    is_helpful: bool = Field(default=True)
    comment: Optional[str] = Field(default=None)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )


class CopilotConversation(SQLModel, table=True):
    __tablename__ = "copilot_conversations"
    __table_args__ = (
        Index("idx_copilot_conv_user_id", "user_id"),
        Index("idx_copilot_conv_created_at", "created_at"),
        {"extend_existing": True}
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user_profiles.id", index=True)
    title: str = Field(max_length=200, default="New conversation")
    context_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn(JSONB, server_default=text("'{}'"))
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )

    messages: List["CopilotMessage"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "CopilotMessage.created_at"}
    )


class CopilotMessage(SQLModel, table=True):
    __tablename__ = "copilot_messages"
    __table_args__ = (
        Index("idx_copilot_msg_conv_id", "conversation_id"),
        {"extend_existing": True}
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="copilot_conversations.id", index=True)
    role: str = Field(max_length=20)  # "user" | "assistant"
    content: str  # Plain text or markdown
    artifacts: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn(JSONB, server_default=text("'{}'"))
    )
    tokens_used: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )

    conversation: CopilotConversation = Relationship(back_populates="messages")

