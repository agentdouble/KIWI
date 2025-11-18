from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, bindparam
from typing import List, Optional
from uuid import UUID
import logging
import re

from app.database import get_db
from app.config import settings
from app.schemas.search import SearchRequest, SearchResponse, SearchHit
from app.models import Document, EntityType as ModelEntityType
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import embedding_service
from app.utils.auth import get_optional_current_user
from app.models.user import User

router = APIRouter(tags=["search"])
logger = logging.getLogger(__name__)


def _build_snippet(text: str, query: str, max_chars: int = 400) -> str:
    """Return a short excerpt centred around the first query term match."""
    if not text:
        return ""

    stripped = text.strip()
    if len(stripped) <= max_chars:
        return stripped

    # Extract meaningful tokens from the query
    terms = [
        token
        for token in re.split(r"\W+", query.lower())
        if len(token) >= 3
    ]

    haystack = stripped.lower()
    match_index = -1
    for term in terms:
        idx = haystack.find(term)
        if idx != -1:
            match_index = idx
            break

    if match_index == -1:
        snippet = stripped[:max_chars].rstrip()
        return snippet + ("…" if len(stripped) > max_chars else "")

    half_window = max_chars // 2
    start = max(match_index - half_window, 0)
    end = min(start + max_chars, len(stripped))
    # Re-adjust start in case we hit the end boundary first
    start = max(0, end - max_chars)

    snippet = stripped[start:end].strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(stripped):
        snippet += "…"
    return snippet


@router.post("/search", response_model=SearchResponse)
async def semantic_search(req: SearchRequest, db: AsyncSession = Depends(get_db), current_user: Optional[User] = Depends(get_optional_current_user)):
    # Vérifier que l'entité existe
    # Pour AGENT: facultatif (public / owner) – on ne bloque pas ici.
    # Pour CHAT: vérifier existence
    requested_entity_type = ModelEntityType(req.entity_type.value)

    if requested_entity_type == ModelEntityType.CHAT:
        from app.models.chat import Chat
        result = await db.execute(select(Chat).where(Chat.id == req.entity_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Chat non trouvé")

    # Embedding de la requête
    qvec = await embedding_service.embed_query(req.query)
    if not qvec:
        raise HTTPException(status_code=500, detail="Embedding de requête vide")

    hits: List[SearchHit] = []

    # Essayer pgvector
    used_pgvector = False
    if settings.pgvector_enabled:
        try:
            vec_literal = embedding_service.to_pgvector_literal(qvec)
            # Optimisation ANN
            try:
                probes = int(settings.pgvector_ivfflat_probes)
                # Les GUC ne supportent pas les bind params avec asyncpg; injecter la valeur littérale
                await db.execute(text(f"SET LOCAL ivfflat.probes = {probes}"))
            except Exception as e:
                # Paramètre GUC absent si pgvector non chargé; rollback et basculer en fallback
                logger.debug(f"ivfflat.probes SET LOCAL failed: {e}")
                await db.rollback()
                raise
            query = text(
                """
                SELECT dc.id::uuid   AS chunk_id,
                       d.id::uuid    AS document_id,
                       d.name        AS document_name,
                       dc.chunk_index,
                       dc.content,
                       d.processed_path,
                       (dc.embedding_vec <=> :qvec::vector) AS distance
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE d.entity_type = :entity_type
                  AND d.entity_id = :entity_id::uuid
                  AND dc.embedding_vec IS NOT NULL
                ORDER BY dc.embedding_vec <=> :qvec::vector
                LIMIT :k
                """
            ).bindparams(
                bindparam("qvec"),
                bindparam("entity_type"),
                bindparam("entity_id"),
                bindparam("k"),
            )
            res = await db.execute(
                query,
                {
                    "qvec": vec_literal,
                    "entity_type": requested_entity_type.value,
                    "entity_id": str(req.entity_id),
                    "k": req.top_k,
                },
            )
            rows = res.mappings().all()
            for r in rows:
                distance = float(r["distance"])
                score = 1.0 - distance
                if req.min_score is not None and score < req.min_score:
                    continue
                hits.append(
                    SearchHit(
                        chunk_id=r["chunk_id"],
                        document_id=r["document_id"],
                        document_name=r["document_name"],
                        chunk_index=r["chunk_index"],
                        content=_build_snippet(r["content"], req.query),
                        distance=distance,
                        score=score,
                        processed_path=r["processed_path"],
                    )
                )
            # Considère pgvector « utilisé » uniquement si on a des résultats
            used_pgvector = len(hits) > 0
        except Exception as e:
            # Important: rollback la transaction sinon toute requête suivante échoue
            logger.warning(f"pgvector search failed, will fallback to JSONB: {e}")
            try:
                await db.rollback()
            except Exception:
                pass
            used_pgvector = False

    # Fallback JSONB + cosine Python
    if not used_pgvector:
        # Charger les chunks et embeddings JSONB
        res = await db.execute(
            select(DocumentChunk, Document)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.entity_type == requested_entity_type)
            .where(Document.entity_id == req.entity_id)
        )
        rows = res.all()
        def cosine(a: List[float], b: List[float]) -> float:
            import math
            if not a or not b:
                return 0.0
            s = sum(x*y for x, y in zip(a, b))
            na = math.sqrt(sum(x*x for x in a))
            nb = math.sqrt(sum(y*y for y in b))
            if na == 0 or nb == 0:
                return 0.0
            return s / (na * nb)
        scored: List[tuple[float, DocumentChunk, Document]] = []
        for dc, d in rows:
            vec = dc.embedding or []
            sim = cosine(qvec, vec)
            scored.append((sim, dc, d))
        scored.sort(key=lambda t: t[0], reverse=True)
        for sim, dc, d in scored[: req.top_k]:
            if req.min_score is not None and sim < req.min_score:
                continue
            hits.append(
                SearchHit(
                    chunk_id=dc.id,
                    document_id=d.id,
                    document_name=d.name,
                    chunk_index=dc.chunk_index,
                    content=_build_snippet(dc.content or "", req.query),
                    distance=1.0 - float(sim),
                    score=float(sim),
                    processed_path=d.processed_path,
                )
            )

    return SearchResponse(query=req.query, hits=hits)
