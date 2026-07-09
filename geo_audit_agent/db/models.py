import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any

import sqlmodel
from sqlalchemy import JSON, DateTime, Index, MetaData, text
from sqlalchemy import Column as SAColumn
from sqlmodel import Field, Relationship, SQLModel

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
    display_name: str | None = Field(default=None, max_length=100)
    plan_tier: str = Field(default="free", max_length=20)
    monthly_audit_quota: int = Field(default=10)
    tier: str = Field(default="free", max_length=50)
    tier_expires_at: datetime | None = None
    stripe_customer_id: str | None = Field(default=None, max_length=255)
    stripe_subscription_id: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )

    brands: list["Brand"] = Relationship(back_populates="owner")


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
    website_url: str | None = Field(default=None, max_length=500)
    metadata_: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn("metadata", JSONB, server_default=text("'{}'"))
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )

    owner: UserProfile = Relationship(back_populates="brands")
    audits: list["Audit"] = Relationship(
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
    llm_response: str | None = Field(default=None)
    is_cited: bool = Field(default=False)
    confidence_score: float = Field(default=0.0)
    sentiment: str | None = Field(default=None, max_length=20)

    # Structured results (JSONB)
    gaps: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=SAColumn(JSONB, server_default=text("'[]'"))
    )
    planned_actions: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn(JSONB, server_default=text("'{}'"))
    )
    remediations: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn(JSONB, server_default=text("'{}'"))
    )
    competitors: list[str] = Field(
        default_factory=list,
        sa_column=SAColumn(JSONB, server_default=text("'[]'"))
    )
    anomalies: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn(JSONB, server_default=text("'{}'"))
    )
    report: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn(JSONB, server_default=text("'{}'"))
    )

    # Predictive scoring
    predicted_geo_score: float | None = Field(default=None)

    # Cost tracking
    total_tokens: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)

    # Temporal workflow reference
    workflow_run_id: str | None = Field(default=None, max_length=100)

    # Timestamps
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )

    brand: Brand = Relationship(back_populates="audits")
    feedback: list["AuditFeedback"] = Relationship(back_populates="audit")


# ── Feedback ──

class AuditFeedback(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "audit_feedback"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    audit_id: uuid.UUID = Field(foreign_key="audits.id", index=True)
    user_id: uuid.UUID = Field(foreign_key="user_profiles.id", index=True)
    feedback_type: str = Field(max_length=20)
    nps_score: int | None = Field(default=None, ge=0, le=10)
    comment: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )

    audit: Audit = Relationship(back_populates="feedback")


# ── Competitor Scans ──

class Competitor(SQLModel, table=True):
    __tablename__ = "competitors"
    __table_args__ = (
        Index("idx_competitors_brand_id", "brand_id"),
        {"extend_existing": True}
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_id: uuid.UUID = Field(foreign_key="brands.id", index=True)
    name: str = Field(max_length=255)
    website: str | None = Field(default=None, max_length=500)
    category: str = Field(default="", max_length=100)
    city: str = Field(default="", max_length=100)
    is_auto_discovered: bool = Field(default=True)
    added_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )


class CompetitorScan(SQLModel, table=True):
    __tablename__ = "competitor_scans"
    __table_args__ = (
        {"extend_existing": True},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    competitor_id: uuid.UUID = Field(foreign_key="competitors.id", index=True)
    scan_type: str = Field(default="weekly", max_length=20)
    status: str = Field(default="pending", max_length=20)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None)
    crawl_data: dict[str, Any] = Field(
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
    details: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn("details", JSONB, server_default=text("'{}'"))
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )


class CompetitorExplanation(SQLModel, table=True):
    __tablename__ = "competitor_explanations"
    __table_args__ = (
        {"extend_existing": True},
    )

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
    __tablename__ = "alerts"
    __table_args__ = (
        {"extend_existing": True},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user_profiles.id", index=True)
    competitor_id: uuid.UUID | None = Field(default=None, foreign_key="competitors.id", index=True)
    alert_type: str = Field(max_length=50)
    severity: str = Field(default="info", max_length=20)
    message: str = Field(default="")
    is_read: bool = Field(default=False)
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
    context_snapshot: dict[str, Any] = Field(
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

    messages: list["CopilotMessage"] = Relationship(
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
    artifacts: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn(JSONB, server_default=text("'{}'"))
    )
    tokens_used: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )

    conversation: CopilotConversation = Relationship(back_populates="messages")



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
    category: str | None = Field(default=None, max_length=50)
    blocked: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )


# ── Agentic system tables ──

class PlanStatus(str, Enum):
    PENDING = "pending"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETE = "complete"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ActionPlan(SQLModel, table=True):
    __tablename__ = "action_plans"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    brand_id: uuid.UUID = Field(foreign_key="brands.id", index=True)
    audit_id: uuid.UUID | None = Field(default=None, index=True)
    plan_data: dict[str, Any] = Field(default_factory=dict, sa_column=SAColumn(JSONB))
    status: str = Field(default=PlanStatus.PENDING, max_length=20, index=True)
    approved_by: uuid.UUID | None = Field(default=None, foreign_key="user_profiles.id")
    approved_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()")))


class ActionExecution(SQLModel, table=True):
    __tablename__ = "action_executions"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    plan_id: uuid.UUID | None = Field(default=None, foreign_key="action_plans.id", index=True)
    action_id: str = Field(max_length=100)
    status: str = Field(default="pending", max_length=20)
    result: dict[str, Any] = Field(default_factory=dict, sa_column=SAColumn(JSONB))
    error_message: str | None = Field(default=None)
    executed_at: datetime = Field(default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()")))


class InspectorCheck(SQLModel, table=True):
    __tablename__ = "inspector_checks"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_id: str = Field(max_length=50, index=True)
    trace_id: str | None = Field(default=None, index=True, max_length=100)
    check_type: str = Field(max_length=50)
    input_data: dict[str, Any] = Field(default_factory=dict, sa_column=SAColumn(JSONB))
    result: dict[str, Any] = Field(default_factory=dict, sa_column=SAColumn(JSONB))
    passed: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()")))


class GuardrailViolation(SQLModel, table=True):
    __tablename__ = "guardrail_violations"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    guardrail_type: str = Field(max_length=50, index=True)
    agent_id: str | None = Field(default=None, max_length=50)
    trace_id: str | None = Field(default=None, index=True, max_length=100)
    violation_details: dict[str, Any] = Field(default_factory=dict, sa_column=SAColumn(JSONB))
    severity: str = Field(default="medium", max_length=20)
    blocked: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()")))


class AgentTrace(SQLModel, table=True):
    __tablename__ = "agent_traces"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_id: str = Field(max_length=50, index=True)
    trace_id: str = Field(max_length=100, index=True)
    context: dict[str, Any] = Field(default_factory=dict, sa_column=SAColumn(JSONB))
    decision: dict[str, Any] = Field(default_factory=dict, sa_column=SAColumn(JSONB))
    outcome: dict[str, Any] = Field(default_factory=dict, sa_column=SAColumn(JSONB))
    score: float | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()")))


class ImprovementProposal(SQLModel, table=True):
    __tablename__ = "improvement_proposals"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_id: str = Field(max_length=50, index=True)
    proposal_type: str = Field(max_length=50)
    description: str
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=SAColumn(JSONB))
    before_score: float | None = Field(default=None)
    after_score: float | None = Field(default=None)
    status: str = Field(default="pending", max_length=20, index=True)
    deployed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()")))


class BillingHistory(SQLModel, table=True):
    __tablename__ = "billing_history"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user_profiles.id", index=True)
    tier: str = Field(max_length=50)
    amount: float
    currency: str = Field(default="usd", max_length=3)
    payment_method: str = Field(default="card", max_length=20)
    status: str = Field(max_length=20)
    stripe_invoice_id: str | None = Field(default=None, max_length=255)
    stripe_payment_intent_id: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditUsage(SQLModel, table=True):
    __tablename__ = "audit_usage"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user_profiles.id", index=True)
    audit_date: date = Field(default_factory=date.today)
    count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InvoiceRequest(SQLModel, table=True):
    __tablename__ = "invoice_requests"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user_profiles.id", index=True)
    tier: str = Field(max_length=50)
    amount: float
    status: str = Field(default="pending", max_length=20)  # pending, sent, paid, cancelled
    invoice_sent_at: datetime | None = Field(default=None)
    paid_at: datetime | None = Field(default=None)
    notes: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

