from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from fastapi import HTTPException, status

from app.models.agent import Agent
from app.models.user import User
from app.schemas.agent import CreateAgentRequest, UpdateAgentRequest
import logging

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_visible_agents(self, current_user: Optional[User]) -> List[Agent]:
        query = select(Agent).where(Agent.is_active == True)
        
        if current_user:
            query = query.where(
                or_(
                    Agent.is_public == True,
                    Agent.user_id == current_user.id
                )
            )
        else:
            query = query.where(Agent.is_public == True)
        
        result = await self.db.execute(query.order_by(Agent.created_at.desc()))
        return result.scalars().all()
    
    async def get_default_agents(self) -> List[Agent]:
        result = await self.db.execute(
            select(Agent)
            .where(and_(Agent.is_public == True, Agent.is_default == True))
            .order_by(Agent.created_at)
        )
        return result.scalars().all()
    
    async def create_agent(self, agent_data: CreateAgentRequest, user_id: UUID) -> Agent:
        agent = Agent(
            name=agent_data.name,
            description=agent_data.description,
            system_prompt=agent_data.system_prompt,
            category=agent_data.category,
            user_id=user_id,
            is_public=agent_data.is_public,
            is_active=True,
            tags=agent_data.tags or []
        )
        
        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)
        
        logger.info(f"Agent created: {agent.id} by user {user_id}")
        return agent
    
    async def get_agent_by_id(self, agent_id: UUID, current_user: Optional[User]) -> Agent:
        result = await self.db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        if not agent.is_public and (not current_user or agent.user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return agent
    
    async def update_agent(self, agent_id: UUID, update_data: UpdateAgentRequest, user_id: UUID) -> Agent:
        agent = await self.get_agent_by_id(agent_id, None)
        
        if agent.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owner can update this agent"
            )
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(agent, field, value)
        
        await self.db.commit()
        await self.db.refresh(agent)
        
        logger.info(f"Agent updated: {agent_id}")
        return agent
    
    async def delete_agent(self, agent_id: UUID, user_id: UUID) -> None:
        agent = await self.get_agent_by_id(agent_id, None)
        
        if agent.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owner can delete this agent"
            )
        
        await self.db.delete(agent)
        await self.db.commit()
        
        logger.info(f"Agent deleted: {agent_id}")
    
    @staticmethod
    def agent_to_dict(agent: Agent) -> dict:
        return {
            "id": str(agent.id),
            "name": agent.name,
            "description": agent.description,
            "system_prompt": agent.system_prompt,
            "category": agent.category,
            "is_public": agent.is_public,
            "user_id": str(agent.user_id) if agent.user_id else None,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
            "is_active": agent.is_active,
            "tags": agent.tags or [],
            "is_default": getattr(agent, 'is_default', False)
        }