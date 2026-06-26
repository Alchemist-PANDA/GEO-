"""add copilot tables

Revision ID: b01ababa7828
Revises: 91560ccbdaef
Create Date: 2026-06-26 03:12:35.181553

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b01ababa7828'
down_revision: Union[str, Sequence[str], None] = '91560ccbdaef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('copilot_conversations',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
    sa.Column('context_snapshot', sa.JSON(), server_default=sa.text("'{}'"), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(now())'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(now())'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user_profiles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_copilot_conv_created_at', 'copilot_conversations', ['created_at'], unique=False)
    op.create_index('idx_copilot_conv_user_id', 'copilot_conversations', ['user_id'], unique=False)
    op.create_index(op.f('ix_copilot_conversations_user_id'), 'copilot_conversations', ['user_id'], unique=False)

    op.create_table('copilot_messages',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('conversation_id', sa.Uuid(), nullable=False),
    sa.Column('role', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
    sa.Column('content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('artifacts', sa.JSON(), server_default=sa.text("'{}'"), nullable=True),
    sa.Column('tokens_used', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(now())'), nullable=True),
    sa.ForeignKeyConstraint(['conversation_id'], ['copilot_conversations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_copilot_msg_conv_id', 'copilot_messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_copilot_messages_conversation_id'), 'copilot_messages', ['conversation_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_copilot_messages_conversation_id'), table_name='copilot_messages')
    op.drop_index('idx_copilot_msg_conv_id', table_name='copilot_messages')
    op.drop_table('copilot_messages')
    op.drop_index(op.f('ix_copilot_conversations_user_id'), table_name='copilot_conversations')
    op.drop_index('idx_copilot_conv_user_id', table_name='copilot_conversations')
    op.drop_index('idx_copilot_conv_created_at', table_name='copilot_conversations')
    op.drop_table('copilot_conversations')

