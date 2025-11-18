from __future__ import annotations

import logging
from typing import List, Sequence
from threading import Lock

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, text

from app.config import settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.utils.chunking import split_text_into_chunks

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EmbeddingService:
    def __init__(self):
        self.chunk_size = settings.embedding_chunk_size_chars
        self.chunk_overlap = settings.embedding_chunk_overlap
        self.batch_size = settings.embedding_batch_size
        self.provider = settings.embedding_provider
        self.model = settings.embedding_model
        self.local_model_path = settings.embedding_local_model_path
        if self.provider == "local" and self.local_model_path:
            self.model = self.local_model_path
        self._local_model = None
        self._local_model_lock = Lock()
        self._pgvector_supported = True

    async def embed_document_text(
        self,
        db: AsyncSession,
        document: Document,
        text: str,
    ) -> List[DocumentChunk]:
        """
        Découpe le texte, calcule les embeddings (Mistral) et upsert en DB.
        """
        chunks = split_text_into_chunks(
            text,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        if not chunks:
            logger.info(f"No chunks generated for document {document.id}")
            return []

        # Nettoyage préalable: supprimer anciens chunks si re-traitement
        await db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
        )
        await db.flush()

        # Embeddings en lots
        embeddings = await self._embed_texts(chunks)

        objs: List[DocumentChunk] = []
        for idx, (content, vector) in enumerate(zip(chunks, embeddings)):
            obj = DocumentChunk(
                document_id=document.id,
                chunk_index=idx,
                content=content,
                embedding=vector,
                embedding_model=self.model,
            )
            db.add(obj)
            objs.append(obj)

        await db.commit()
        # rafraîchir pour ids
        for o in objs:
            await db.refresh(o)
        logger.info(
            f"Stored {len(objs)} chunks with embeddings for document {document.id}"
        )

        # Essayez d'hydrater la colonne pgvector si disponible
        await self._maybe_write_pgvector(db, objs)
        return objs

    async def _maybe_write_pgvector(self, db: AsyncSession, chunks: List[DocumentChunk]) -> None:
        """Écrit embedding_vec (pgvector) si la colonne existe. Utilise un cast ::vector.
        Cette méthode n'échoue pas le flux en cas d'erreur; elle log uniquement.
        """
        if not chunks or not self._pgvector_supported:
            return
        try:
            # Vérifier existence de la colonne embedding_vec
            # On tente une simple commande no-op qui échoue si la colonne n'existe pas
            await db.execute(text("SELECT 1 FROM document_chunks LIMIT 1"))
            # Mise à jour par lot
            for chunk in chunks:
                vec = chunk.embedding or []
                vec_str = '[' + ','.join(f"{x:.6f}" for x in vec) + ']'
                await db.execute(
                    text(
                        "UPDATE document_chunks SET embedding_vec = CAST(:vec AS vector) WHERE id = :id"
                    ),
                    {"vec": vec_str, "id": str(chunk.id)},
                )
            await db.commit()
            logger.info("pgvector column embedding_vec populated for %d chunks", len(chunks))
        except Exception as e:
            await db.rollback()
            message = str(e)
            if "type \"vector\" does not exist" in message:
                logger.warning(
                    "pgvector extension not installed; skipping future pgvector writes. Detail: %s",
                    message,
                )
                self._pgvector_supported = False
            else:
                logger.warning("Could not write pgvector embeddings (non-blocking): %s", message)

    async def _embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        if self.provider == "mistral":
            return await self._embed_with_mistral(texts)
        if self.provider == "local":
            return await self._embed_with_local_model(texts)
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    async def _embed_with_mistral(self, texts: Sequence[str]) -> List[List[float]]:
        """Appel batch à l'API Mistral Embeddings."""
        from mistralai import Mistral

        client = Mistral(api_key=settings.mistral_api_key)
        all_vectors: List[List[float]] = []

        # Batching avec réduction adaptative si l'API refuse un lot trop grand
        effective_batch = max(1, int(self.batch_size) or 32)
        pos = 0
        prefers_input = True

        while pos < len(texts):
            end = min(pos + effective_batch, len(texts))
            batch = list(texts[pos:end])
            try:
                try:
                    resp = await _to_thread(
                        client.embeddings.create,
                        model=self.model,
                        input=batch,
                    )
                except TypeError:
                    resp = await _to_thread(
                        client.embeddings.create,
                        model=self.model,
                        inputs=batch,
                    )
                vectors = [item.embedding for item in resp.data]
                all_vectors.extend(vectors)
                pos = end  # avancer
            except Exception as e:
                msg = str(e)
                # Réduction adaptative si l'API renvoie "Batch size too large"
                if "Batch size too large" in msg or "invalid_request_batch_error" in msg:
                    if effective_batch <= 1:
                        # Impossible de réduire davantage, re-raise
                        raise
                    effective_batch = max(1, effective_batch // 2)
                    logger.warning("Embedding batch too large, reducing to %d", effective_batch)
                    continue  # réessayer le même pos avec batch réduit
                # Autre erreur: relancer
                raise

        return all_vectors

    def _ensure_local_model(self):
        if self._local_model is not None:
            return self._local_model

        with self._local_model_lock:
            if self._local_model is None:
                model_path = self.local_model_path or self.model
                if not model_path:
                    raise ValueError("No local embedding model path configured")
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError as exc:  # pragma: no cover - dependency guard
                    raise RuntimeError(
                        "sentence-transformers is required for EMBEDDING_PROVIDER=local. "
                        "Add it to your environment."
                    ) from exc

                logger.info("Loading local embedding model from %s", model_path)
                self._local_model = SentenceTransformer(
                    model_path,
                    device="cpu",
                )
        return self._local_model

    async def _embed_with_local_model(self, texts: Sequence[str]) -> List[List[float]]:
        model = self._ensure_local_model()

        all_vectors: List[List[float]] = []
        effective_batch = max(1, int(self.batch_size) or 8)
        pos = 0

        while pos < len(texts):
            end = min(pos + effective_batch, len(texts))
            batch = list(texts[pos:end])

            vectors_array = await _to_thread(
                model.encode,
                batch,
                batch_size=effective_batch,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=False,
            )

            all_vectors.extend(vectors_array.tolist())
            pos = end

        return all_vectors

    async def embed_query(self, text: str) -> List[float]:
        """Calcule l'embedding d'une requête (taille 1024)."""
        vectors = await self._embed_texts([text])
        return vectors[0] if vectors else []

    @staticmethod
    def to_pgvector_literal(vec: List[float]) -> str:
        """Convertit une liste de floats en littéral texte pgvector: '[0.1,0.2,...]'"""
        return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"


async def _to_thread(fn, /, *args, **kwargs):
    """Utilitaire pour appeler une fonction sync dans un thread."""
    import asyncio

    return await asyncio.to_thread(fn, *args, **kwargs)


embedding_service = EmbeddingService()
