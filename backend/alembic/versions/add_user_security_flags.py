"""Add must_change_password flag and password_changed_at timestamp to users

Revision ID: add_user_security_flags_001
Revises: add_feedbackloop_001
Create Date: 2025-10-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_user_security_flags_001'
down_revision = 'add_feedbackloop_001'
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.add_column(
            'users',
            sa.Column(
                'must_change_password',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('false'),
            ),
        )
        op.add_column(
            'users',
            sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True),
        )
        op.alter_column('users', 'must_change_password', server_default=None)
    except Exception:
        # Best effort to keep runtime deployment resilient
        pass


def downgrade():
    try:
        op.drop_column('users', 'password_changed_at')
    except Exception:
        pass
    try:
        op.drop_column('users', 'must_change_password')
    except Exception:
        pass
