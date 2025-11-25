import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import aiofiles
from datetime import datetime
import uuid
import mimetypes
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text
from fastapi import UploadFile, HTTPException

from app.models.document import Document, EntityType, ProcessingStatus
from app.config import settings
from app.utils.document_processors import process_document_to_text
from app.services.embedding_service import embedding_service
from app.utils.schema import ensure_document_processing_schema
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class DocumentService:
    def __init__(self):
        self.storage_path = Path(settings.storage_path)
        self.max_file_size = settings.max_file_size_mb * 1024 * 1024
        self._enums_normalized = False
        self._schema_verified = False

    async def _ensure_schema(self) -> None:
        if self._schema_verified:
            return

        try:
            await ensure_document_processing_schema()
            self._schema_verified = True
        except Exception as exc:
            logger.exception("Schema verification failed")
            self._schema_verified = False
        
    async def _update_processing_metadata(
        self,
        db: AsyncSession,
        document: Document,
        update: Dict[str, Any],
    ) -> None:
        """Persist incremental processing metadata for UI feedback."""
        metadata = dict(document.document_metadata or {})

        stage = update.get("stage")
        if stage:
            metadata["processing_stage"] = stage

        stage_label = update.get("stage_label")
        if stage_label:
            metadata["stage_label"] = stage_label

        message = update.get("message") or update.get("stage_message")
        if message is not None:
            metadata["stage_message"] = message

        current = update.get("current")
        total = update.get("total")
        if current is not None:
            metadata["current_step"] = current
        if total is not None:
            metadata["total_steps"] = total

        progress = update.get("progress")
        if progress is None and current is not None and total:
            try:
                progress = max(0.0, min(1.0, float(current) / float(total)))
            except Exception:
                progress = None
        if progress is not None:
            try:
                new_progress = max(0.0, min(1.0, float(progress)))
            except Exception:
                new_progress = None
            if new_progress is not None:
                existing_progress = metadata.get("progress")
                if isinstance(existing_progress, (int, float)):
                    new_progress = max(float(existing_progress), new_progress)
                metadata["progress"] = new_progress

        metadata["updated_at"] = datetime.utcnow().isoformat()

        document.document_metadata = metadata

        try:
            await db.commit()
            await db.refresh(document)
        except Exception as exc:
            logger.warning("Failed to update document %s metadata: %s", document.id, exc)
            try:
                await db.rollback()
            except Exception:
                pass
    def _get_storage_path(self, entity_type: EntityType, entity_id: str, doc_id: str, is_processed: bool = False) -> Path:
        base_path = self.storage_path / "documents" / entity_type.slug / entity_id
        if is_processed:
            return base_path / "processed" / f"{doc_id}.txt"
        else:
            return base_path / "raw" / doc_id
    
    def _validate_file(self, file: UploadFile) -> None:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nom de fichier manquant")
        
        ext = Path(file.filename).suffix.lower()
        if ext not in settings.allowed_file_types:
            raise HTTPException(
                status_code=415,
                detail=f"Format non pris en charge. Types acceptés: {', '.join(settings.allowed_file_types)}"
            )
        
        # Tenter d'identifier le type MIME, avec des fallbacks sûrs
        mime_type = mimetypes.guess_type(file.filename)[0]
        if not mime_type:
            fallback_map = {
                ".pdf": "application/pdf",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".doc": "application/msword",
                ".rtf": "application/rtf",
                ".txt": "text/plain",
                ".md": "text/markdown",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            mime_type = fallback_map.get(ext)
        # Si toujours inconnu, utiliser un type générique au lieu d'échouer
        if not mime_type:
            mime_type = "application/octet-stream"
    
    async def upload_document(
        self, 
        db: AsyncSession,
        file: UploadFile,
        entity_type: EntityType,
        entity_id: str,
        uploaded_by: Optional[str] = None,
        name: Optional[str] = None,
        auto_process: bool = False
    ) -> Document:
        await self._ensure_schema()
        await self._ensure_enums_normalized(db)
        logger.info(f"Starting document upload: {file.filename} for {entity_type.slug} {entity_id}")
        self._validate_file(file)
        
        if entity_type == EntityType.AGENT:
            count = await self._count_entity_documents(db, entity_type, entity_id)
            if count >= settings.max_documents_per_agent:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Limite de {settings.max_documents_per_agent} documents atteinte pour cet agent"
                )
        elif entity_type == EntityType.CHAT:
            count = await self._count_entity_documents(db, entity_type, entity_id)
            if count >= settings.max_documents_per_chat:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Limite de {settings.max_documents_per_chat} documents atteinte pour ce chat"
                )
        
        doc_id = str(uuid.uuid4())
        storage_path = self._get_storage_path(entity_type, entity_id, doc_id)
        
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_size = 0
        try:
            logger.info(f"Saving file: {storage_path}")
            async with aiofiles.open(storage_path, 'wb') as f:
                while chunk := await file.read(8192):
                    file_size += len(chunk)
                    if file_size > self.max_file_size:
                        await aiofiles.os.remove(storage_path)
                        raise HTTPException(
                            status_code=413,
                            detail=f"Fichier trop volumineux. Taille max: {settings.max_file_size_mb}MB"
                        )
                    await f.write(chunk)
            logger.info(f"File saved: {file_size} bytes")
        except Exception as e:
            if storage_path.exists():
                storage_path.unlink()
            raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")
        
        document = Document(
            id=uuid.UUID(doc_id),
            name=name or Path(file.filename).stem,
            original_filename=file.filename,
            file_type=mimetypes.guess_type(file.filename)[0] or 'application/octet-stream',
            file_size=file_size,
            storage_path=str(storage_path.relative_to(self.storage_path)),
            entity_type=entity_type,
            entity_id=uuid.UUID(entity_id),
            uploaded_by=uuid.UUID(uploaded_by) if uploaded_by else None,
            processing_status=ProcessingStatus.PENDING,
            document_metadata={
                "processing_stage": "queued",
                "stage_label": "En attente du traitement",
                "progress": 0.0,
            },
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)

        if not auto_process:
            # Laisser le traitement à une tâche de fond
            return document
        else:
            try:
                logger.info(f"Starting document processing for {document.id}")
                # Marquer PROCESSING avant le traitement long
                document.processing_status = ProcessingStatus.PROCESSING
                await db.commit()
                await db.refresh(document)

                processed_doc = await self.process_document(db, str(document.id))
                logger.info(f"Document {document.id} processed successfully")
                return processed_doc
            except Exception as e:
                logger.error(f"Error processing document {document.id}: {str(e)}")
                # Marquer FAILED
                document.processing_status = ProcessingStatus.FAILED
                document.processing_error = str(e)
                await db.commit()
                await db.refresh(document)
                return document
    
    async def process_document(self, db: AsyncSession, document_id: str) -> Document:
        await self._ensure_schema()
        await self._ensure_enums_normalized(db)
        logger.info(f"Starting document processing for {document_id}")
        document = await self.get_document(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document non trouvé")

        doc_logging_id = document_id

        logger.info(f"Document: {document.name} ({document.file_type})")
        # Marquer le document en cours de traitement si pas déjà fait
        try:
            document.processing_status = ProcessingStatus.PROCESSING
            document.processing_error = None
            await db.commit()
            await db.refresh(document)
        except Exception:
            pass

        # Indiquer la préparation du document
        await self._update_processing_metadata(
            db,
            document,
            {
                "stage": "preparing",
                "stage_label": "Préparation du document",
                "progress": 0.02,
                "message": "Initialisation du traitement",
            },
        )

        logger.info(f"Processing document...")
        
        raw_path = self.storage_path / document.storage_path
        processed_path = self._get_storage_path(
            document.entity_type, 
            str(document.entity_id), 
            str(document.id), 
            is_processed=True
        )
        
        processed_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Calling processor for {document.file_type}")
            if 'image' in document.file_type or document.original_filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                logger.info("Processing image with configured vision model")
            elif document.original_filename.lower().endswith('.pdf'):
                logger.info("Processing PDF (text extraction + vision model if needed)")

            async def progress_callback(update: Dict[str, Any]):
                try:
                    await self._update_processing_metadata(db, document, update)
                except Exception as meta_exc:
                    logger.debug(
                        "Progress callback failed for document %s: %s",
                        document.id,
                        meta_exc,
                    )

            await progress_callback({
                "stage": "text_extraction",
                "stage_label": "Extraction du texte",
                "progress": 0.05,
                "message": "Lecture du contenu",
            })

            text_content = await process_document_to_text(
                str(raw_path),
                document.file_type,
                progress_callback=progress_callback,
            )
            logger.info(f"Extracted text: {len(text_content)} characters")
            
            async with aiofiles.open(processed_path, 'w', encoding='utf-8') as f:
                await f.write(text_content)
            logger.info(f"Text saved to: {processed_path}")
            
            # Sauvegarder le chemin traité, mais ne pas marquer COMPLETED tant que les embeddings ne sont pas prêts
            document.processed_path = str(processed_path.relative_to(self.storage_path))
            document.processed_at = datetime.utcnow()
            document.processing_error = None
            
            await db.commit()
            await db.refresh(document)
            logger.info(f"Text extracted and saved for document {document.id}; generating embeddings...")

            await progress_callback({
                "stage": "text_extraction",
                "stage_label": "Extraction du texte",
                "progress": 0.8,
                "message": "Extraction terminée",
            })

            await progress_callback({
                "stage": "embedding",
                "stage_label": "Indexation des connaissances",
                "progress": 0.9,
                "message": "Calcul des embeddings",
            })

            # Étape RAG: créer les embeddings et stocker les chunks
            try:
                logger.info(f"Embedding chunks for document {doc_logging_id}...")
                _ = await embedding_service.embed_document_text(db, document, text_content)
                logger.info(f"Embeddings stored for document {doc_logging_id}")
                # Marquer COMPLETED seulement après embeddings OK
                document.processing_status = ProcessingStatus.COMPLETED
                document.processing_error = None
                await db.commit()
                await db.refresh(document)

                await progress_callback({
                    "stage": "completed",
                    "stage_label": "Traitement terminé",
                    "progress": 1.0,
                    "message": "Document indexé avec succès",
                })
            except Exception as ee:
                logger.error(
                    "Embedding error for document %s: %s",
                    doc_logging_id,
                    str(ee),
                    exc_info=True,
                )
                document.processing_status = ProcessingStatus.FAILED
                document.processing_error = str(ee)
                await db.commit()
                await db.refresh(document)

                await progress_callback({
                    "stage": "failed",
                    "stage_label": "Erreur lors de l'indexation",
                    "progress": 1.0,
                    "message": str(ee),
                })
            
            return document
        except Exception as e:
            logger.error("Processing error for document %s: %s", document_id, str(e), exc_info=True)
            document.processing_status = ProcessingStatus.FAILED
            document.processing_error = str(e)
            await db.commit()
            await db.refresh(document)
            await self._update_processing_metadata(
                db,
                document,
                {
                    "stage": "failed",
                    "stage_label": "Erreur de traitement",
                    "progress": 1.0,
                    "message": str(e),
                },
            )
            raise HTTPException(status_code=500, detail=f"Erreur lors du traitement: {str(e)}")
    
    async def get_document(self, db: AsyncSession, document_id: str) -> Optional[Document]:
        await self._ensure_schema()
        result = await db.execute(
            select(Document).where(Document.id == uuid.UUID(document_id))
        )
        return result.scalar_one_or_none()
    
    async def get_document_content(self, db: AsyncSession, document_id: str) -> Optional[str]:
        document = await self.get_document(db, document_id)
        if not document:
            return None
        
        if document.processed_path:
            processed_file = self.storage_path / document.processed_path
            if processed_file.exists():
                async with aiofiles.open(processed_file, 'r', encoding='utf-8') as f:
                    return await f.read()
        
        return None
    
    async def list_entity_documents(
        self, 
        db: AsyncSession, 
        entity_type: EntityType, 
        entity_id: str
    ) -> List[Document]:
        await self._ensure_schema()
        await self._ensure_enums_normalized(db)
        result = await db.execute(
            select(Document)
            .where(
                and_(
                    Document.entity_type == entity_type,
                    Document.entity_id == uuid.UUID(entity_id)
                )
            )
            .order_by(Document.created_at.desc())
        )
        return result.scalars().all()
    
    async def delete_document(self, db: AsyncSession, document_id: str) -> bool:
        await self._ensure_schema()
        document = await self.get_document(db, document_id)
        if not document:
            return False
        
        raw_path = self.storage_path / document.storage_path
        if raw_path.exists():
            raw_path.unlink()
        
        if document.processed_path:
            processed_path = self.storage_path / document.processed_path
            if processed_path.exists():
                processed_path.unlink()
        
        await db.delete(document)
        await db.commit()
        
        return True
    
    async def _count_entity_documents(
        self, 
        db: AsyncSession, 
        entity_type: EntityType, 
        entity_id: str
    ) -> int:
        await self._ensure_schema()
        result = await db.execute(
            select(Document)
            .where(
                and_(
                    Document.entity_type == entity_type,
                    Document.entity_id == uuid.UUID(entity_id)
                )
            )
        )
        return len(result.scalars().all())


    async def _ensure_enums_normalized(self, db: AsyncSession) -> None:
        """Normalize enum values stored in PostgreSQL to match expected casing."""
        if self._enums_normalized:
            return

        try:
            await self._ensure_schema()
            await db.execute(
                text(
                    "UPDATE documents "
                    "SET processing_status = upper(processing_status::text)::processingstatus "
                    "WHERE processing_status::text != upper(processing_status::text)"
                )
            )
            await db.execute(
                text(
                    "UPDATE documents "
                    "SET entity_type = upper(entity_type::text)::entitytype "
                    "WHERE entity_type::text != upper(entity_type::text)"
                )
            )
            await db.commit()
            self._enums_normalized = True
        except Exception as exc:
            logger.debug("Enum normalization skipped: %s", exc)
            await db.rollback()
            self._enums_normalized = False

document_service = DocumentService()
