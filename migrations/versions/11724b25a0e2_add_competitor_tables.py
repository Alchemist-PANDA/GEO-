"""Add competitor tables

Revision ID: 11724b25a0e2
Revises: 11724b25a0e1
Create Date: 2026-06-25 14:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11724b25a0e2'
down_revision: Union[str, Sequence[str], None] = '11724b25a0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'competitors',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('brand_id', sa.Uuid(), sa.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('website', sa.String(500)),
        sa.Column('category', sa.String(100), server_default=''),
        sa.Column('city', sa.String(100), server_default=''),
        sa.Column('is_auto_discovered', sa.Boolean, server_default='true'),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index('idx_competitors_brand_id', 'competitors', ['brand_id'])

    op.create_table(
        'competitor_scans',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('competitor_id', sa.Uuid(), sa.ForeignKey('competitors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scan_type', sa.String(20), server_default='weekly'),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('error_message', sa.Text),
        sa.Column('crawl_data', sa.JSON(), server_default=sa.text("'{}'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        'competitor_scores',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('competitor_id', sa.Uuid(), sa.ForeignKey('competitors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scan_id', sa.Uuid(), sa.ForeignKey('competitor_scans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dimension', sa.String(50)),
        sa.Column('score', sa.Float, server_default='0.0'),
        sa.Column('details', sa.JSON(), server_default=sa.text("'{}'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index('idx_scores_competitor_scan', 'competitor_scores', ['competitor_id', 'scan_id'])

    op.create_table(
        'competitor_explanations',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('competitor_id', sa.Uuid(), sa.ForeignKey('competitors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scan_id', sa.Uuid(), sa.ForeignKey('competitor_scans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('explanation_type', sa.String(50)),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('confidence', sa.Float, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        'alerts',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('user_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('competitor_id', sa.Uuid(), sa.ForeignKey('competitors.id', ondelete='CASCADE'), nullable=True),
        sa.Column('alert_type', sa.String(50)),
        sa.Column('severity', sa.String(20), server_default='info'),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('is_read', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table('alerts')
    op.drop_table('competitor_explanations')
    op.drop_index('idx_scores_competitor_scan', table_name='competitor_scores')
    op.drop_table('competitor_scores')
    op.drop_table('competitor_scans')
    op.drop_index('idx_competitors_brand_id', table_name='competitors')
    op.drop_table('competitors')
