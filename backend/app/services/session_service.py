from typing import List, Optional
from uuid import UUID
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.session import Session
from app.models.chat import Chat
from app.schemas.chat import CreateChatRequest
from app.services.chat_service import ChatService
import logging

logger = logging.getLogger(__name__)


class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_session(self) -> Session:
        session = Session(
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(f"Session created: {session.id}")
        return session
    
    async def validate_session(self, session_id: UUID) -> bool:
        result = await self.db.execute(
            select(Session)
            .where(and_(Session.id == session_id, Session.is_active == True))
        )
        session = result.scalar_one_or_none()
        return session is not None
    
    async def deactivate_session(self, session_id: UUID) -> None:
        result = await self.db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session.is_active = False
        await self.db.commit()
        
        logger.info(f"Session deactivated: {session_id}")
    
    async def get_session_chats(self, session_id: UUID, user_id: UUID) -> List[Chat]:
        if not await self.validate_session(session_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or inactive"
            )
        
        result = await self.db.execute(
            select(Chat)
            .where(and_(
                Chat.session_id == session_id,
                Chat.user_id == user_id,
                Chat.is_active == True
            ))
            .options(selectinload(Chat.agent))
            .order_by(Chat.created_at.desc())
        )
        return result.scalars().all()
    
    async def create_session_chat(
        self, 
        session_id: UUID, 
        chat_data: CreateChatRequest, 
        user_id: UUID
    ) -> Chat:
        if not await self.validate_session(session_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or inactive"
            )
        
        chat_service = ChatService(self.db)
        chat = await chat_service.create_chat(chat_data, user_id)
        
        chat.session_id = session_id
        await self.db.commit()
        await self.db.refresh(chat)
        
        logger.info(f"Chat {chat.id} created in session {session_id}")
        return chat