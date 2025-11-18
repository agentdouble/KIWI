from sqlalchemy import Column, String, Text, Boolean, DateTime, ARRAY, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import uuid

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    system_prompt = Column(Text, nullable=False)
    avatar = Column(String(50))
    avatar_image = Column(Text)
    is_default = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Relation avec l'utilisateur créateur (obligatoire)
    user_id = Column(UUID(as_uuid=True), ForeignKey('app_users.id'), nullable=False)
    
    # Configuration LLM
    model = Column(String(100), default="mistral-small-latest")
    category = Column(String(50), default='general')
    capabilities = Column(ARRAY(Text), default=list)
    tags = Column(ARRAY(Text), default=list)
    parameters = Column(JSONB, default={
        "temperature": 0.7,
        "maxTokens": 4000,
        "topP": 0.9
    })
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    user = relationship("User", back_populates="agents")
    chats = relationship("Chat", back_populates="agent", cascade="all, delete-orphan")
    favorited_by = relationship("AgentFavorite", back_populates="agent", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', user_id={self.user_id})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "avatar": self.avatar,
            "avatar_image": self.avatar_image,
            "is_default": self.is_default,
            "is_public": self.is_public,
            "is_active": self.is_active,
            "user_id": str(self.user_id),
            "model": self.model,
            "category": self.category,
            "capabilities": self.capabilities,
            "tags": self.tags,
            "parameters": self.parameters,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AgentFavorite(Base):
    __tablename__ = "agent_favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('app_users.id', ondelete='CASCADE'), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="favorite_agents")
    agent = relationship("Agent", back_populates="favorited_by")

    __table_args__ = (
        UniqueConstraint('user_id', 'agent_id', name='uq_agent_favorites_user_agent'),
    )

    def __repr__(self) -> str:
        return f"<AgentFavorite(user_id={self.user_id}, agent_id={self.agent_id})>"
