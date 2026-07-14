"""agentic system tables

Revision ID: 0007_agentic
Revises: b01ababa7828
"""
import sqlalchemy as sa
from alembic import op

revision = "0007_agentic"
down_revision = "b01ababa7828"
branch_labels = None
depends_on = None

def _ts():
    return sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))

def upgrade():
    op.create_table("action_plans",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("brand_id", sa.Uuid(), sa.ForeignKey("brands.id", ondelete="CASCADE")),
        sa.Column("audit_id", sa.Uuid(), nullable=True),
        sa.Column("plan_data", sa.JSON(), server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("approved_by", sa.Uuid(), sa.ForeignKey("user_profiles.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        _ts())
    op.create_index("idx_action_plans_brand_id", "action_plans", ["brand_id"])

    op.create_table("action_executions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("plan_id", sa.Uuid(), sa.ForeignKey("action_plans.id", ondelete="CASCADE")),
        sa.Column("action_id", sa.String(100)),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("result", sa.JSON()), sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")))
    op.create_index("idx_action_executions_plan_id", "action_executions", ["plan_id"])

    op.create_table("inspector_checks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("agent_id", sa.String(50)), sa.Column("trace_id", sa.String(100), nullable=True),
        sa.Column("check_type", sa.String(50)),
        sa.Column("input_data", sa.JSON()), sa.Column("result", sa.JSON()),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("true")), _ts())
    op.create_index("idx_inspector_checks_agent_id", "inspector_checks", ["agent_id"])

    op.create_table("guardrail_violations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("guardrail_type", sa.String(50)), sa.Column("agent_id", sa.String(50), nullable=True),
        sa.Column("trace_id", sa.String(100), nullable=True),
        sa.Column("violation_details", sa.JSON()), sa.Column("severity", sa.String(20), server_default="medium"),
        sa.Column("blocked", sa.Boolean(), server_default=sa.text("false")), _ts())
    op.create_index("idx_guardrail_violations_type", "guardrail_violations", ["guardrail_type"])

    op.create_table("agent_traces",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("agent_id", sa.String(50)), sa.Column("trace_id", sa.String(100)),
        sa.Column("context", sa.JSON()), sa.Column("decision", sa.JSON()), sa.Column("outcome", sa.JSON()),
        sa.Column("score", sa.Float(), nullable=True), _ts())
    op.create_index("idx_agent_traces_agent_id", "agent_traces", ["agent_id"])
    op.create_index("idx_agent_traces_trace_id", "agent_traces", ["trace_id"])

    op.create_table("improvement_proposals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("agent_id", sa.String(50)), sa.Column("proposal_type", sa.String(50)),
        sa.Column("description", sa.Text()), sa.Column("payload", sa.JSON()),
        sa.Column("before_score", sa.Float(), nullable=True), sa.Column("after_score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=True), _ts())
    op.create_index("idx_improvement_proposals_status", "improvement_proposals", ["status"])

def downgrade():
    for t in ["improvement_proposals", "agent_traces", "guardrail_violations",
              "inspector_checks", "action_executions", "action_plans"]:
        op.drop_table(t)
