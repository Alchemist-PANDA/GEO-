"""add competitor feedback

Revision ID: 91560ccbdaef
Revises: 11724b25a0e2
Create Date: 2026-06-25 15:24:36.427123

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91560ccbdaef'
down_revision: Union[str, Sequence[str], None] = '11724b25a0e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('competitor_feedback',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('competitor_id', sa.Uuid(), nullable=False),
    sa.Column('is_helpful', sa.Boolean(), nullable=False),
    sa.Column('comment', sa.String(length=1000), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(now())'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user_profiles.id'], ),
    sa.ForeignKeyConstraint(['competitor_id'], ['competitors.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_competitor_feedback_competitor_id'), 'competitor_feedback', ['competitor_id'], unique=False)
    op.create_index(op.f('ix_competitor_feedback_user_id'), 'competitor_feedback', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_competitor_feedback_user_id'), table_name='competitor_feedback')
    op.drop_index(op.f('ix_competitor_feedback_competitor_id'), table_name='competitor_feedback')
    op.drop_table('competitor_feedback')
