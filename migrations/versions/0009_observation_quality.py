"""store observation sentiment and measurement confidence

Revision ID: 0009_observation_quality
Revises: 0008_evidence
"""

import sqlalchemy as sa
from alembic import op

revision = "0009_observation_quality"
down_revision = "0008_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("observation_evidence", sa.Column("sentiment", sa.String(length=20), nullable=True))
    op.add_column(
        "observation_evidence",
        sa.Column("measurement_confidence", sa.Float(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("observation_evidence", "measurement_confidence")
    op.drop_column("observation_evidence", "sentiment")
