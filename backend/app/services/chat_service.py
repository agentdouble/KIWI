from typing import List, Optional
from uuid import UUID
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.chat import Chat
from app.models.agent import Agent
from app.models.message import Message
from app.schemas.chat import CreateChatRequest
import logging

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_chats(self, user_id: UUID) -> List[Chat]:
        result = await self.db.execute(
            select(Chat)
            .where(and_(Chat.user_id == user_id, Chat.is_active == True))
            .options(selectinload(Chat.agent))
            .order_by(desc(Chat.last_message_at))
        )
        return result.scalars().all()
    
    async def create_chat(self, chat_data: CreateChatRequest, user_id: UUID) -> Chat:
        agent_id = chat_data.agent_id
        
        if not agent_id:
            default_agent = await self.get_or_create_default_agent(user_id)
            agent_id = default_agent.id
        else:
            agent_result = await self.db.execute(
                select(Agent).where(Agent.id == agent_id)
            )
            agent = agent_result.scalar_one_or_none()
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found"
                )
        
        chat = Chat(
            title=chat_data.title or "Nouvelle conversation",
            agent_id=agent_id,
            user_id=user_id,
            is_active=True,
            last_message_at=datetime.utcnow()
        )
        
        self.db.add(chat)
        await self.db.commit()
        await self.db.refresh(chat)
        
        logger.info(f"Chat created: {chat.id} for user {user_id}")
        return chat
    
    async def get_chat_by_id(self, chat_id: UUID, user_id: UUID) -> Chat:
        result = await self.db.execute(
            select(Chat)
            .where(and_(Chat.id == chat_id, Chat.user_id == user_id))
            .options(selectinload(Chat.messages), selectinload(Chat.agent))
        )
        chat = result.scalar_one_or_none()
        
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        return chat
    
    async def update_chat_title(self, chat_id: UUID, title: str, user_id: UUID) -> Chat:
        chat = await self.get_chat_by_id(chat_id, user_id)
        
        chat.title = title
        await self.db.commit()
        await self.db.refresh(chat)
        
        logger.info(f"Chat title updated: {chat_id}")
        return chat
    
    async def delete_chat(self, chat_id: UUID, user_id: UUID) -> None:
        chat = await self.get_chat_by_id(chat_id, user_id)
        
        chat.is_active = False
        await self.db.commit()
        
        logger.info(f"Chat deactivated: {chat_id}")
    
    async def get_or_create_default_agent(self, user_id: UUID) -> Agent:
        result = await self.db.execute(
            select(Agent)
            .where(and_(
                Agent.user_id == user_id,
                Agent.name == "Assistant par défaut",
                Agent.is_active == True
            ))
        )
        agent = result.scalar_one_or_none()
        
        if not agent:
            agent = Agent(
                name="Assistant par défaut",
                description="Votre assistant personnel",
                system_prompt="Tu es un assistant IA serviable et professionnel.",
                category="general",
                user_id=user_id,
                is_public=False,
                is_active=True,
                tags=["default", "personal"]
            )
            self.db.add(agent)
            await self.db.commit()
            await self.db.refresh(agent)
            logger.info(f"Default agent created for user {user_id}")
        
        return agent