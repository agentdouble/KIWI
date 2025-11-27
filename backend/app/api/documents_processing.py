from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

from app.models.document import Document, EntityType
from app.utils.dependencies import get_db, get_current_session
from app.services.document_service import document_service
from sqlalchemy import text
from app.config import settings

router = APIRouter(prefix="/documents", tags=["document-processing"])

@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    session = Depends(get_current_session)
):
    """
    Relance le traitement d'un document, utile pour régénérer les transcripts d'images avec le modèle de vision configuré
    """
    # Vérifier que le document existe
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    # Vérifier les permissions
    if document.entity_type == EntityType.AGENT:
        # Pour les agents, vérifier que l'utilisateur est le propriétaire
        from app.services.agent_service import agent_service
        agent = await agent_service.get_agent(db, str(document.entity_id))
        if not agent:
            raise HTTPException(status_code=404, detail="Agent non trouvé")
        # Pour l'instant, on ne vérifie pas les permissions d'ownership
    
    # Lancer le retraitement en arrière-plan
    background_tasks.add_task(document_service.process_document, db, document_id)
    
    return {
        "message": "Retraitement du document lancé", 
        "document_id": document_id,
        "document_name": document.name
    }

@router.post("/reprocess-all-images")
async def reprocess_all_images(
    entity_type: Optional[EntityType] = None,
    entity_id: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    session = Depends(get_current_session)
):
    """
    Relance le traitement de toutes les images pour régénérer les transcripts avec le modèle de vision configuré
    """
    from sqlalchemy import select, and_, or_
    
    # Construire la requête pour trouver toutes les images
    query = select(Document).where(
        or_(
            Document.file_type.like('image/%'),
            Document.original_filename.like('%.png'),
            Document.original_filename.like('%.jpg'),
            Document.original_filename.like('%.jpeg'),
            Document.original_filename.like('%.gif'),
            Document.original_filename.like('%.webp')
        )
    )
    
    # Filtrer par entité si spécifié
    if entity_type and entity_id:
        query = query.where(
            and_(
                Document.entity_type == entity_type,
                Document.entity_id == uuid.UUID(entity_id)
            )
        )
    
    # Exécuter la requête
    result = await db.execute(query)
    documents = result.scalars().all()
    
    # Lancer le retraitement pour chaque document
    count = 0
    for doc in documents:
        # Vérifier les permissions pour chaque document
        if doc.entity_type == EntityType.AGENT:
            from app.services.agent_service import agent_service
            agent = await agent_service.get_agent(db, str(doc.entity_id))
            if agent:
                background_tasks.add_task(document_service.process_document, db, str(doc.id))
                count += 1
        elif doc.entity_type == EntityType.CHAT:
            # Pour les chats, on peut traiter tous les documents
            background_tasks.add_task(document_service.process_document, db, str(doc.id))
            count += 1
    
    return {
        "message": f"Retraitement lancé pour {count} images",
        "total_images_found": len(documents),
        "images_processed": count
    }


@router.get("/vector-status")
async def vector_status(db: AsyncSession = Depends(get_db)):
    """Vérifie la présence de l'extension pgvector, de la colonne embedding_vec et de l'index.
    Retourne également le nombre de chunks avec embedding_vec non NULL.
    """
    status = {
        "pgvector_extension": False,
        "embedding_vec_column": False,
        "ivfflat_index": False,
        "populated_rows": 0,
        "embedding_dimension": settings.embedding_dimension,
    }

    try:
        # Extension
        res = await db.execute(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"))
        status["pgvector_extension"] = bool(res.scalar())

        # Colonne
        res = await db.execute(text(
            """
            SELECT EXISTS (
              SELECT 1 FROM information_schema.columns
              WHERE table_name='document_chunks' AND column_name='embedding_vec'
            )
            """
        ))
        status["embedding_vec_column"] = bool(res.scalar())

        # Index
        res = await db.execute(text(
            """
            SELECT EXISTS (
              SELECT 1 FROM pg_indexes
              WHERE schemaname = current_schema()
                AND tablename = 'document_chunks'
                AND indexname = 'idx_document_chunks_embedding_vec'
            )
            """
        ))
        status["ivfflat_index"] = bool(res.scalar())

        # Population
        if status["embedding_vec_column"]:
            res = await db.execute(text("SELECT COUNT(*) FROM document_chunks WHERE embedding_vec IS NOT NULL"))
            status["populated_rows"] = int(res.scalar() or 0)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector status check failed: {str(e)}")

    return status
