from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.chat import Chat
from app.models.message import Message
from app.models.user import User
from app.models.agent import Agent
from app.schemas.chat import ChatResponse, CreateChatRequest
from app.schemas.message import MessageResponse
from app.utils.auth import get_optional_current_user, get_current_active_user
import uuid
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# Route pour récupérer tous les chats de l'utilisateur connecté
@router.get("/", response_model=List[ChatResponse])
async def get_user_chats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Récupérer tous les chats d'un utilisateur connecté"""
    query = (
        select(Chat)
        .options(
            selectinload(Chat.messages).selectinload(Message.feedback_entries),
            selectinload(Chat.agent)
        )
        .where(Chat.user_id == current_user.id)
        .where(Chat.is_active == True)
        .order_by(Chat.last_message_at.desc().nullslast(), Chat.created_at.desc())
    )
    
    result = await db.execute(query)
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
                    chat_id=str(msg.chat_id),
                    feedback=next(
                        (entry.feedback_type for entry in msg.feedback_entries if entry.user_id == current_user.id),
                        None
                    )
                ) for msg in sorted(chat.messages, key=lambda m: m.created_at)
            ],
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            agent_id=str(chat.agent_id),
            session_id=None  # Plus de sessions dans le nouveau schéma
        ) for chat in chats
    ]

@router.post("/", response_model=ChatResponse)
async def create_chat(
    request: CreateChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Créer un nouveau chat"""
    # Gérer agent_id de manière plus robuste
    agent_id = None
    if request.agent_id and request.agent_id != "null" and request.agent_id != "undefined":
        try:
            agent_id = uuid.UUID(request.agent_id)
        except ValueError:
            # Si ce n'est pas un UUID valide, ignorer
            pass
    
    # Si pas d'agent spécifié, utiliser l'agent par défaut de l'utilisateur
    if not agent_id:
        result = await db.execute(
            select(Agent)
            .where(Agent.user_id == current_user.id)
            .where(Agent.is_default == True)
            .where(Agent.is_active == True)
        )
        default_agent = result.scalar_one_or_none()
        if default_agent:
            agent_id = default_agent.id
        else:
            # Si pas d'agent par défaut, prendre le premier agent de l'utilisateur
            result = await db.execute(
                select(Agent)
                .where(Agent.user_id == current_user.id)
                .where(Agent.is_active == True)
                .order_by(Agent.created_at.asc())
            )
            first_agent = result.scalar_one_or_none()
            if first_agent:
                agent_id = first_agent.id
    
    if not agent_id:
        raise HTTPException(status_code=400, detail="Aucun agent disponible pour créer un chat")
    
    chat = Chat(
        title=request.title or "Nouveau chat",
        agent_id=agent_id,
        user_id=current_user.id,
        is_active=True,
        is_archived=False
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
        agent_id=str(chat.agent_id),
        session_id=None  # Plus de sessions dans le nouveau schéma
    )

@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Récupérer un chat spécifique avec ses messages"""
    result = await db.execute(
        select(Chat)
        .where(Chat.id == uuid.UUID(chat_id))
        .where(Chat.user_id == current_user.id)
        .options(selectinload(Chat.messages).selectinload(Message.feedback_entries))
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return ChatResponse(
        id=str(chat.id),
        title=chat.title,
        messages=[
            MessageResponse(
                id=str(msg.id),
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                chat_id=str(msg.chat_id),
                feedback=next(
                    (entry.feedback_type for entry in msg.feedback_entries if entry.user_id == current_user.id),
                    None
                )
            ) for msg in sorted(chat.messages, key=lambda m: m.created_at)
        ],
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        agent_id=str(chat.agent_id),
        session_id=None  # Plus de sessions dans le nouveau schéma
    )

class UpdateChatRequest(BaseModel):
    title: str

@router.patch("/{chat_id}")
async def update_chat_title(
    chat_id: str,
    request: UpdateChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mettre à jour le titre d'un chat"""
    result = await db.execute(
        select(Chat)
        .where(Chat.id == uuid.UUID(chat_id))
        .where(Chat.user_id == current_user.id)
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat.title = request.title
    await db.commit()
    await db.refresh(chat)
    
    return ChatResponse(
        id=str(chat.id),
        title=chat.title,
        messages=[],
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        agent_id=str(chat.agent_id),
        session_id=None  # Plus de sessions dans le nouveau schéma
    )

@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Archiver un chat (suppression logique)"""
    result = await db.execute(
        select(Chat)
        .where(Chat.id == uuid.UUID(chat_id))
        .where(Chat.user_id == current_user.id)
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat.is_active = False
    await db.commit()

    return {"message": "Chat archived successfully"}
