"""add_tier_pricing_tables

Revision ID: a04831d5d2e7
Revises: 0007_agentic
Create Date: 2026-07-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'a04831d5d2e7'
down_revision: Union[str, None] = '0007_agentic'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create audit_usage
    op.create_table('audit_usage',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('audit_date', sa.Date(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_usage_user_id'), 'audit_usage', ['user_id'], unique=False)
    
    # 2. Create billing_history
    op.create_table('billing_history',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('tier', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sqlmodel.sql.sqltypes.AutoString(length=3), nullable=False),
        sa.Column('payment_method', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('stripe_invoice_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('stripe_payment_intent_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_billing_history_user_id'), 'billing_history', ['user_id'], unique=False)

    # 3. Add columns to user_profiles
    with op.batch_alter_table('user_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tier', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True, server_default='free'))
        batch_op.add_column(sa.Column('tier_expires_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('stripe_customer_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
        batch_op.add_column(sa.Column('stripe_subscription_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))

def downgrade() -> None:
    pass
