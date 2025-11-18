"""Create agent favorites table and remove global favorite flag

Revision ID: add_agent_favorites_001
Revises: add_pgvector_001
Create Date: 2025-01-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_agent_favorites_001'
down_revision = 'add_pgvector_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    try:
        op.drop_column('agents', 'is_favorite')
    except Exception:
        pass

    op.create_table(
        'agent_favorites',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['app_users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'agent_id', name='uq_agent_favorites_user_agent'),
    )


def downgrade() -> None:
    op.drop_table('agent_favorites')
    try:
        op.add_column('agents', sa.Column('is_favorite', sa.Boolean(), server_default=sa.false(), nullable=False))
        op.alter_column('agents', 'is_favorite', server_default=None)
    except Exception:
        pass
