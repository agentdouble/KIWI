"""Create feedbackloop table for message reactions

Revision ID: add_feedbackloop_001
Revises: add_agent_favorites_001
Create Date: 2025-10-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_feedbackloop_001'
down_revision = 'add_agent_favorites_001'
branch_labels = None
depends_on = None


FEEDBACK_TYPE_CONSTRAINT = 'check_feedbackloop_type'
UNIQUE_CONSTRAINT = 'uq_feedbackloop_message_user'


def upgrade() -> None:
    op.create_table(
        'feedbackloop',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_type', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id', 'user_id', name=UNIQUE_CONSTRAINT),
        sa.CheckConstraint("feedback_type IN ('up', 'down')", name=FEEDBACK_TYPE_CONSTRAINT),
    )

    op.create_index('ix_feedbackloop_message', 'feedbackloop', ['message_id'])
    op.create_index('ix_feedbackloop_user', 'feedbackloop', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_feedbackloop_user', table_name='feedbackloop')
    op.drop_index('ix_feedbackloop_message', table_name='feedbackloop')
    op.drop_table('feedbackloop')
