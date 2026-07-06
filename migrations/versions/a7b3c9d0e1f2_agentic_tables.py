"""Add agentic AI tables

Revision ID: a7b3c9d0e1f2
Revises: 11724b25a0e1
Create Date: 2026-06-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'a7b3c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = '11724b25a0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('action_plans',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('brand_id', sa.Uuid(), nullable=False),
        sa.Column('audit_id', sa.Uuid(), nullable=True),
        sa.Column('plan_data', sa.JSON(), nullable=True),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('approved_by', sa.Uuid(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['user_profiles.id']),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_action_plans_brand_id'), 'action_plans', ['brand_id'])
    op.create_index(op.f('ix_action_plans_audit_id'), 'action_plans', ['audit_id'])
    op.create_index(op.f('ix_action_plans_status'), 'action_plans', ['status'])

    op.create_table('action_executions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('plan_id', sa.Uuid(), nullable=True),
        sa.Column('action_id', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['action_plans.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_action_executions_plan_id'), 'action_executions', ['plan_id'])

    op.create_table('inspector_checks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('agent_id', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('trace_id', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('check_type', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_inspector_checks_agent_id'), 'inspector_checks', ['agent_id'])
    op.create_index(op.f('ix_inspector_checks_trace_id'), 'inspector_checks', ['trace_id'])
    op.create_index(op.f('ix_inspector_checks_passed'), 'inspector_checks', ['passed'])

    op.create_table('guardrail_violations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('guardrail_type', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('agent_id', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('trace_id', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('violation_details', sa.JSON(), nullable=True),
        sa.Column('severity', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('blocked', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_guardrail_violations_guardrail_type'), 'guardrail_violations', ['guardrail_type'])
    op.create_index(op.f('ix_guardrail_violations_trace_id'), 'guardrail_violations', ['trace_id'])
    op.create_index(op.f('ix_guardrail_violations_blocked'), 'guardrail_violations', ['blocked'])

    op.create_table('agent_traces',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('agent_id', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('trace_id', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('decision', sa.JSON(), nullable=True),
        sa.Column('outcome', sa.JSON(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_agent_traces_agent_id'), 'agent_traces', ['agent_id'])
    op.create_index(op.f('ix_agent_traces_trace_id'), 'agent_traces', ['trace_id'])

    op.create_table('improvement_proposals',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('agent_id', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('proposal_type', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('before_score', sa.Float(), nullable=True),
        sa.Column('after_score', sa.Float(), nullable=True),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_improvement_proposals_agent_id'), 'improvement_proposals', ['agent_id'])
    op.create_index(op.f('ix_improvement_proposals_status'), 'improvement_proposals', ['status'])


def downgrade() -> None:
    op.drop_table('improvement_proposals')
    op.drop_table('agent_traces')
    op.drop_table('guardrail_violations')
    op.drop_table('inspector_checks')
    op.drop_table('action_executions')
    op.drop_table('action_plans')
