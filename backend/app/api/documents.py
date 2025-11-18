from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.database import get_db, AsyncSessionLocal
from app.utils.auth import get_current_active_user, get_optional_current_user, is_user_admin
from app.utils.dependencies import get_current_session
from app.utils.rate_limit import limiter, UPLOAD_RATE_LIMIT
from app.models import EntityType, User, Session
from app.schemas.document import (
    DocumentResponse, 
    DocumentListResponse, 
    DocumentContentResponse,
    DocumentUpload
)
from app.services.document_service import document_service
from app.config import settings

router = APIRouter(tags=["documents"])


async def _process_document_background(document_id: str):
    """Ouvre une session DB dédiée et lance le traitement du document."""
    async with AsyncSessionLocal() as session:
        try:
            await document_service.process_document(session, document_id)
        except Exception:
            # process_document journalise et met à jour le statut en cas d'échec
            pass

@router.post("/agents/{agent_id}/documents", response_model=DocumentResponse)
@limiter.limit(UPLOAD_RATE_LIMIT)
async def upload_agent_document(
    request: Request,
    agent_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)  # Changé pour optionnel
):
    """Upload un document pour un agent"""
    # Vérifier que l'agent existe
    from app.models import Agent
    from sqlalchemy import select
    
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    
    # Vérifier que l'utilisateur est le propriétaire de l'agent (si authentifié)
    if current_user and agent.user_id != current_user.id and not is_user_admin(current_user):
        raise HTTPException(status_code=403, detail="Vous ne pouvez modifier que vos propres agents")
    elif not current_user:
        # Pour les tests sans auth - À SUPPRIMER EN PRODUCTION
        print("⚠️  ATTENTION: Upload sans authentification - À supprimer en production")
    
    # Upload le document (sans traitement immédiat)
    document = await document_service.upload_document(
        db=db,
        file=file,
        entity_type=EntityType.AGENT,
        entity_id=str(agent_id),
        uploaded_by=str(current_user.id) if current_user else None,
        name=name,
        auto_process=False,
    )

    # Lancer le traitement en arrière-plan
    background_tasks.add_task(_process_document_background, str(document.id))
    
    return document

@router.get("/agents/{agent_id}/documents", response_model=DocumentListResponse)
async def list_agent_documents(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Liste les documents d'un agent"""
    # Vérifier que l'agent existe
    from app.models import Agent
    from sqlalchemy import select
    
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    
    # Vérifier les permissions - l'agent doit être public, par défaut, ou appartenir à l'utilisateur
    is_admin = is_user_admin(current_user)

    if not agent.is_public and not agent.is_default:
        if current_user and agent.user_id != current_user.id and not is_admin:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        elif not current_user:
            # Pour les tests sans auth - À SUPPRIMER EN PRODUCTION
            print("⚠️  ATTENTION: Listing sans authentification - À supprimer en production")
    
    # Récupérer les documents
    documents = await document_service.list_entity_documents(
        db=db,
        entity_type=EntityType.AGENT,
        entity_id=str(agent_id)
    )
    
    return DocumentListResponse(
        documents=documents,
        total=len(documents)
    )

@router.post("/chats/{chat_id}/documents", response_model=DocumentResponse)
@limiter.limit(UPLOAD_RATE_LIMIT)
async def upload_chat_document(
    request: Request,
    chat_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Upload un document pour un chat"""
    # Vérifier que le chat existe
    from app.models import Chat
    from sqlalchemy import select
    
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id)
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat non trouvé")
    
    # Vérifier que l'utilisateur a accès au chat (si authentifié)
    if current_user and chat.user_id and chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé à ce chat")
    
    # Upload le document (sans traitement immédiat)
    document = await document_service.upload_document(
        db=db,
        file=file,
        entity_type=EntityType.CHAT,
        entity_id=str(chat_id),
        uploaded_by=None,  # TODO: Implémenter quand le système d'authentification sera en place
        name=name,
        auto_process=False,
    )

    # Lancer le traitement en arrière-plan
    background_tasks.add_task(_process_document_background, str(document.id))
    
    return document

@router.get("/chats/{chat_id}/documents", response_model=DocumentListResponse)
async def list_chat_documents(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Liste les documents d'un chat"""
    # Vérifier que le chat existe
    from app.models import Chat
    from sqlalchemy import select
    
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id)
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat non trouvé")
    
    # Vérifier que l'utilisateur a accès au chat (si authentifié)
    if current_user and chat.user_id and chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès non autorisé à ce chat")
    
    # Récupérer les documents
    documents = await document_service.list_entity_documents(
        db=db,
        entity_type=EntityType.CHAT,
        entity_id=str(chat_id)
    )
    
    return DocumentListResponse(
        documents=documents,
        total=len(documents)
    )

@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Récupère les informations d'un document"""
    document = await document_service.get_document(db, str(document_id))
    
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    # Vérifier les permissions
    if document.entity_type == EntityType.CHAT:
        from app.models import Chat
        from sqlalchemy import select
        result = await db.execute(select(Chat).where(Chat.id == document.entity_id))
        chat = result.scalar_one_or_none()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat non trouvé")
        # Si utilisateur authentifié, vérifier la propriété
        if current_user and chat.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    return document

@router.get("/documents/{document_id}/content", response_model=DocumentContentResponse)
async def get_document_content(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Récupère le contenu traité d'un document"""
    document = await document_service.get_document(db, str(document_id))
    
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    # Vérifier les permissions (même logique que get_document)
    if document.entity_type == EntityType.CHAT:
        from app.models import Chat
        from sqlalchemy import select
        result = await db.execute(select(Chat).where(Chat.id == document.entity_id))
        chat = result.scalar_one_or_none()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat non trouvé")
        if current_user and chat.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # Récupérer le contenu
    content = await document_service.get_document_content(db, str(document_id))
    
    if not content:
        raise HTTPException(status_code=404, detail="Contenu non disponible")
    
    return DocumentContentResponse(
        id=document.id,
        name=document.name,
        content=content,
        file_type=document.file_type,
        processed=document.processed_at is not None
    )

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Supprime un document"""
    document = await document_service.get_document(db, str(document_id))
    
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    # Vérifier les permissions
    if document.entity_type == EntityType.AGENT:
        # Seul le créateur de l'agent peut supprimer les documents
        from app.models import Agent
        from sqlalchemy import select
        
        result = await db.execute(
            select(Agent).where(Agent.id == document.entity_id)
        )
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent non trouvé")
        # TODO: Vérifier les permissions quand le système d'authentification sera en place
            
    elif document.entity_type == EntityType.CHAT:
        from app.models import Chat
        from sqlalchemy import select
        result = await db.execute(select(Chat).where(Chat.id == document.entity_id))
        chat = result.scalar_one_or_none()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat non trouvé")
        if current_user and chat.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    # Supprimer le document
    success = await document_service.delete_document(db, str(document_id))
    
    if not success:
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression")
    
    return {"message": "Document supprimé avec succès"}
@router.get("/documents/supported-types")
async def get_supported_document_types():
    """Expose les extensions supportées et la taille max pour validation frontend."""
    return {
        "allowed_extensions": settings.allowed_file_types,
        "max_file_size_mb": settings.max_file_size_mb,
    }
