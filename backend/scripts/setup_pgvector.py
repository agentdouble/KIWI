#!/usr/bin/env python3
"""
Setup pgvector for document chunks and backfill vectors.

Usage:
  python backend/scripts/setup_pgvector.py [--batch 1000]

Reads DB config from app.config.Settings (env/.env). Works with
DATABASE_URL using async driver by converting it to psycopg2 DSN.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Tuple
from pathlib import Path

# Ensure project root (parent of this file's directory) is on sys.path
THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception as e:  # pragma: no cover
    print("psycopg2 not installed. Please install psycopg2-binary in backend env.")
    raise


def _dsn_from_settings() -> str:
    # Prefer DATABASE_URL if present (convert +asyncpg -> normal)
    dsn = settings.database_url or settings.sync_database_url
    dsn = dsn.replace("+asyncpg", "")
    # Ensure postgresql:// scheme for psycopg2
    if dsn.startswith("postgresql://") or dsn.startswith("postgres://"):
        return dsn
    return settings.sync_database_url


def ensure_pgvector(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()


def ensure_schema(conn) -> None:
    with conn.cursor() as cur:
        # Add column if missing
        cur.execute(
            """
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='document_chunks' AND column_name='embedding_vec'
              ) THEN
                EXECUTE 'ALTER TABLE document_chunks ADD COLUMN embedding_vec vector(' || %s || ')';
              END IF;
            END
            $$;
            """,
            (settings.embedding_dimension,),
        )
        # Create ivfflat index (L2 default) if missing
        cur.execute(
            """
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = current_schema()
                  AND tablename = 'document_chunks'
                  AND indexname = 'idx_document_chunks_embedding_vec'
              ) THEN
                EXECUTE 'CREATE INDEX idx_document_chunks_embedding_vec ON document_chunks '
                     || 'USING ivfflat (embedding_vec) WITH (lists = ' || %s || ')';
              END IF;
            END
            $$;
            """,
            (settings.pgvector_ivfflat_lists,),
        )
        # Create cosine index if missing
        cur.execute(
            """
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = current_schema()
                  AND tablename = 'document_chunks'
                  AND indexname = 'idx_document_chunks_embedding_vec_cos'
              ) THEN
                EXECUTE 'CREATE INDEX idx_document_chunks_embedding_vec_cos ON document_chunks '
                     || 'USING ivfflat (embedding_vec vector_cosine_ops) WITH (lists = ' || %s || ')';
              END IF;
            END
            $$;
            """,
            (settings.pgvector_ivfflat_lists,),
        )
    conn.commit()


def fetch_backfill_batch(conn, limit: int) -> List[Tuple[str, list]]:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id::text AS id, embedding
            FROM document_chunks
            WHERE embedding_vec IS NULL AND embedding IS NOT NULL
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
    # Ensure types
    return [(row["id"], row["embedding"]) for row in rows]


def backfill_vectors(conn, batch_size: int) -> int:
    total = 0
    while True:
        batch = fetch_backfill_batch(conn, batch_size)
        if not batch:
            break
        with conn.cursor() as cur:
            for chunk_id, embedding in batch:
                # Convert list[float] -> string like "[0.1,0.2,...]"
                if not isinstance(embedding, list):
                    continue
                vec_str = "[" + ",".join(f"{float(x):.6f}" for x in embedding) + "]"
                cur.execute(
                    "UPDATE document_chunks SET embedding_vec = %s::vector WHERE id = %s::uuid",
                    (vec_str, chunk_id),
                )
        conn.commit()
        total += len(batch)
        print(f"Backfilled {total} vectors...", flush=True)
    return total


def print_status(conn) -> None:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector') AS pgvector")
        ext = cur.fetchone()["pgvector"]
        cur.execute(
            """
            SELECT EXISTS (
              SELECT 1 FROM information_schema.columns
              WHERE table_name='document_chunks' AND column_name='embedding_vec'
            ) AS has_column
            """
        )
        col = cur.fetchone()["has_column"]
        cur.execute(
            """
            SELECT EXISTS (
              SELECT 1 FROM pg_indexes
              WHERE schemaname = current_schema()
                AND tablename = 'document_chunks'
                AND indexname = 'idx_document_chunks_embedding_vec'
            ) AS has_index
            """
        )
        idx = cur.fetchone()["has_index"]
        cur.execute("SELECT COUNT(*) AS populated FROM document_chunks WHERE embedding_vec IS NOT NULL")
        populated = cur.fetchone()["populated"]

    print("=== pgvector status ===")
    print(f"extension: {ext}")
    print(f"embedding_vec column: {col}")
    print(f"ivfflat index: {idx}")
    print(f"rows with embedding_vec: {populated}")


def main():
    parser = argparse.ArgumentParser(description="Setup pgvector and backfill vectors")
    parser.add_argument("--batch", type=int, default=1000, help="Backfill batch size")
    args = parser.parse_args()

    dsn = _dsn_from_settings()
    print(f"Connecting to DB: {dsn}")
    conn = psycopg2.connect(dsn)
    try:
        ensure_pgvector(conn)
        ensure_schema(conn)
        print_status(conn)
        updated = backfill_vectors(conn, args.batch)
        if updated:
            print_status(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
