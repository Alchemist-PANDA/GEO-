"""add observation evidence

Revision ID: 0008_evidence
Revises: 43c6d4506480
"""

import sqlalchemy as sa
from alembic import op

revision = "0008_evidence"
down_revision = "43c6d4506480"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "observation_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("audit_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("prompt_id", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=30), nullable=False),
        sa.Column("execution_mode", sa.String(length=20), nullable=False),
        sa.Column("raw_response", sa.Text(), nullable=False),
        sa.Column("mentioned", sa.Boolean(), nullable=False),
        sa.Column("recommendation", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("citation_urls", sa.JSON(), server_default=sa.text("'[]'"), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), nullable=False),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.CheckConstraint("position IS NULL OR position >= 1", name="ck_observation_position"),
        sa.ForeignKeyConstraint(["audit_id"], ["audits.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_observation_evidence_audit_id", "observation_evidence", ["audit_id"])
    op.create_index("ix_observation_evidence_provider", "observation_evidence", ["provider"])
    op.create_index("ix_observation_evidence_prompt_id", "observation_evidence", ["prompt_id"])
    op.create_index("ix_observation_evidence_execution_mode", "observation_evidence", ["execution_mode"])
    op.create_index("idx_observation_audit_provider", "observation_evidence", ["audit_id", "provider"])


def downgrade() -> None:
    op.drop_index("idx_observation_audit_provider", table_name="observation_evidence")
    op.drop_index("ix_observation_evidence_execution_mode", table_name="observation_evidence")
    op.drop_index("ix_observation_evidence_prompt_id", table_name="observation_evidence")
    op.drop_index("ix_observation_evidence_provider", table_name="observation_evidence")
    op.drop_index("ix_observation_evidence_audit_id", table_name="observation_evidence")
    op.drop_table("observation_evidence")
