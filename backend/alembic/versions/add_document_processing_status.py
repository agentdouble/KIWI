"""Add processing status to documents

Revision ID: add_doc_proc_status_001
Revises: add_user_auth_001
Create Date: 2025-09-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'add_doc_proc_status_001'
down_revision = 'add_user_auth_001'
branch_labels = None
depends_on = None


def upgrade():
    try:
        processing_enum = sa.Enum('pending', 'processing', 'completed', 'failed', name='processingstatus')
        processing_enum.create(op.get_bind(), checkfirst=True)

        op.add_column('documents', sa.Column('processing_status', processing_enum, nullable=False, server_default='pending'))
        op.add_column('documents', sa.Column('processing_error', sa.Text(), nullable=True))
        op.alter_column('documents', 'processing_status', server_default=None)
    except Exception:
        # Best effort; database may already have columns
        pass


def downgrade():
    try:
        op.drop_column('documents', 'processing_error')
        op.drop_column('documents', 'processing_status')
    except Exception:
        pass
    try:
        processing_enum = sa.Enum(name='processingstatus')
        processing_enum.drop(op.get_bind(), checkfirst=True)
    except Exception:
        pass

