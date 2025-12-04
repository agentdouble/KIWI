from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.session import Session
from app.models.chat import Chat
from app.schemas.session import SessionResponse
from app.schemas.chat import ChatResponse, CreateChatRequest
from app.schemas.message import MessageResponse
from app.utils.auth import get_current_user
from app.services.rbac_service import (
    PERM_CHAT_CREATE,
    PERM_CHAT_READ_OWN,
    user_has_permission,
)
from app.models.user import User
import uuid
from typing import List

router = APIRouter()

@router.post("/", response_model=SessionResponse)
async def create_session(db: AsyncSession = Depends(get_db)):
    """Créer une nouvelle session"""
    session = Session()
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return SessionResponse(
        session_id=str(session.id),
        created_at=session.created_at
    )

@router.get("/{session_id}/validate")
async def validate_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Valider qu'une session existe et est active"""
    result = await db.execute(
        select(Session).where(
            Session.id == uuid.UUID(session_id),
            Session.is_active == True
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or inactive")
    
    return {"valid": True, "session_id": str(session.id)}

@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Supprimer une session"""
    result = await db.execute(
        select(Session).where(Session.id == uuid.UUID(session_id))
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_active = False
    await db.commit()
    
    return {"message": "Session deleted successfully"}

@router.get("/{session_id}/chats", response_model=List[ChatResponse])
async def get_session_chats(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer tous les chats d'une session"""
    if not await user_has_permission(db, current_user, PERM_CHAT_READ_OWN):
        raise HTTPException(status_code=403, detail="You are not allowed to list your chats")
    result = await db.execute(
        select(Chat)
        .where(Chat.user_id == current_user.id)
        .where(Chat.is_active == True)
        .options(selectinload(Chat.messages))
        .order_by(Chat.created_at.desc())
    )
    chats = result.scalars().all()
    
    return [
        ChatResponse(
            id=str(chat.id),
            title=chat.title,
            messages=[
                MessageResponse(
                    id=str(msg.id),
                    role=msg.role,
                    content=msg.content,
                    created_at=msg.created_at,
                    chat_id=str(msg.chat_id)
                ) for msg in chat.messages
            ],
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            agent_id=str(chat.agent_id) if chat.agent_id else None,
            session_id=session_id  # Retourner le session_id reçu pour la compatibilité
        ) for chat in chats
    ]

@router.post("/{session_id}/chats", response_model=ChatResponse)
async def create_session_chat(
    session_id: str,
    request: CreateChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un nouveau chat pour une session"""
    if not await user_has_permission(db, current_user, PERM_CHAT_CREATE):
        raise HTTPException(status_code=403, detail="You are not allowed to create chats")
    # Gérer agent_id de manière plus robuste
    agent_id = None
    if request.agent_id and request.agent_id != "null" and request.agent_id != "undefined":
        try:
            agent_id = uuid.UUID(request.agent_id)
        except ValueError:
            # Si ce n'est pas un UUID valide, ignorer
            pass
    
    # Si pas d'agent spécifié, agent_id reste None (mode généraliste)
    
    chat = Chat(
        user_id=current_user.id,
        title=request.title or "Nouveau chat",
        agent_id=agent_id
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    
    return ChatResponse(
        id=str(chat.id),
        title=chat.title,
        messages=[],
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        agent_id=str(chat.agent_id) if chat.agent_id else None,
        session_id=session_id  # Retourner le session_id reçu pour la compatibilité
    )
