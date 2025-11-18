"""Add user authentication

Revision ID: add_user_auth_001
Revises: 
Create Date: 2025-01-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_user_auth_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Add user_id to agents table
    op.add_column('agents', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_agents_user_id', 'agents', 'users', ['user_id'], ['id'])
    
    # Rename created_by to user_id if it exists
    try:
        op.drop_column('agents', 'created_by')
    except:
        pass
    
    # Add user_id to chats table
    op.add_column('chats', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_chats_user_id', 'chats', 'users', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade():
    # Drop foreign keys and columns
    op.drop_constraint('fk_chats_user_id', 'chats', type_='foreignkey')
    op.drop_column('chats', 'user_id')
    
    op.drop_constraint('fk_agents_user_id', 'agents', type_='foreignkey')
    op.drop_column('agents', 'user_id')
    
    # Drop users table
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')