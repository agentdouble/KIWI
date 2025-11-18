"""Add pgvector extension and embedding_vec to document_chunks

Revision ID: add_pgvector_001
Revises: add_doc_proc_status_001
Create Date: 2025-09-15

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_pgvector_001'
down_revision = 'add_doc_proc_status_001'
branch_labels = None
depends_on = None


def upgrade():
    # Create pgvector extension
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    except Exception:
        pass

    # Add column embedding_vec with configured dimension (default 1024)
    try:
        # Using raw SQL as SQLAlchemy does not know pgvector type by default
        op.execute("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding_vec vector(1024);")
    except Exception:
        pass

    # Create ivfflat index if extension available
    try:
        op.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_vec ON document_chunks USING ivfflat (embedding_vec) WITH (lists = 100);")
    except Exception:
        pass


def downgrade():
    try:
        op.execute("DROP INDEX IF EXISTS idx_document_chunks_embedding_vec;")
    except Exception:
        pass
    try:
        op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS embedding_vec;")
    except Exception:
        pass
    # We do not drop the extension automatically

