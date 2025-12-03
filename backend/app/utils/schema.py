import logging

from sqlalchemy import text

from app.database import engine

logger = logging.getLogger(__name__)


async def ensure_document_processing_schema() -> None:
    """Ensure runtime DB schema matches expected document columns."""
    try:
        # Créer l'extension vector en dehors d'une transaction contrôlée
        try:
            async with engine.connect() as raw_conn:
                autocommit_conn = await raw_conn.execution_options(
                    isolation_level="AUTOCOMMIT"
                )
                await autocommit_conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception as ext:  # pragma: no cover - optional extension
            logger.warning("pgvector extension unavailable or lacks permissions: %s", ext)

        async with engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_type WHERE typname = 'processingstatus'
                        ) THEN
                            CREATE TYPE processingstatus AS ENUM (
                                'PENDING',
                                'PROCESSING',
                                'COMPLETED',
                                'FAILED'
                            );
                        ELSE
                            IF EXISTS (
                                SELECT 1
                                FROM pg_enum e
                                JOIN pg_type t ON t.oid = e.enumtypid
                                WHERE t.typname = 'processingstatus'
                                AND e.enumlabel = 'pending'
                            ) THEN
                                ALTER TYPE processingstatus RENAME VALUE 'pending' TO 'PENDING';
                            END IF;

                            IF EXISTS (
                                SELECT 1
                                FROM pg_enum e
                                JOIN pg_type t ON t.oid = e.enumtypid
                                WHERE t.typname = 'processingstatus'
                                AND e.enumlabel = 'processing'
                            ) THEN
                                ALTER TYPE processingstatus RENAME VALUE 'processing' TO 'PROCESSING';
                            END IF;

                            IF EXISTS (
                                SELECT 1
                                FROM pg_enum e
                                JOIN pg_type t ON t.oid = e.enumtypid
                                WHERE t.typname = 'processingstatus'
                                AND e.enumlabel = 'completed'
                            ) THEN
                                ALTER TYPE processingstatus RENAME VALUE 'completed' TO 'COMPLETED';
                            END IF;

                            IF EXISTS (
                                SELECT 1
                                FROM pg_enum e
                                JOIN pg_type t ON t.oid = e.enumtypid
                                WHERE t.typname = 'processingstatus'
                                AND e.enumlabel = 'failed'
                            ) THEN
                                ALTER TYPE processingstatus RENAME VALUE 'failed' TO 'FAILED';
                            END IF;
                        END IF;
                    END
                    $$;
                    """
                )
            )

            await conn.execute(
                text(
                    """
                    ALTER TABLE IF EXISTS documents
                    ADD COLUMN IF NOT EXISTS processing_status processingstatus
                    DEFAULT 'PENDING'::processingstatus;
                    """
                )
            )

            await conn.execute(
                text(
                    """
                    UPDATE documents
                    SET processing_status = 'PENDING'::processingstatus
                    WHERE processing_status IS NULL;
                    """
                )
            )

            await conn.execute(
                text(
                    """
                    ALTER TABLE IF EXISTS documents
                    ALTER COLUMN processing_status SET NOT NULL;
                    """
                )
            )

            await conn.execute(
                text(
                    """
                    ALTER TABLE IF EXISTS documents
                    ALTER COLUMN processing_status DROP DEFAULT;
                    """
                )
            )

            await conn.execute(
                text(
                    """
                    ALTER TABLE IF EXISTS documents
                    ADD COLUMN IF NOT EXISTS processing_error TEXT;
                    """
                )
            )
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("Failed to ensure document processing schema")


async def ensure_user_security_schema() -> None:
    """Ensure user table has required security columns."""
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    ALTER TABLE IF EXISTS users
                    ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE;
                    """
                )
            )
            await conn.execute(
                text(
                    """
                    UPDATE users
                    SET must_change_password = FALSE
                    WHERE must_change_password IS NULL;
                    """
                )
            )
            await conn.execute(
                text(
                    """
                    ALTER TABLE IF EXISTS users
                    ALTER COLUMN must_change_password SET NOT NULL;
                    """
                )
            )
            await conn.execute(
                text(
                    """
                    ALTER TABLE IF EXISTS users
                    ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMPTZ;
                    """
                )
            )
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("Failed to ensure user security schema")
