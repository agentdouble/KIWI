from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import uuid

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), default='Nouveau chat')
    
    # Relations
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='SET NULL'), nullable=True)
    
    # Métadonnées du chat
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    summary = Column(Text)  # Résumé automatique du chat
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_message_at = Column(DateTime(timezone=True))  # Timestamp du dernier message
    
    # Indexes pour la performance
    __table_args__ = (
        Index('idx_user_active', 'user_id', 'is_active'),           # Pour récupérer les chats actifs d'un utilisateur
        Index('idx_user_last_message', 'user_id', 'last_message_at'),  # Pour trier par dernière activité
        Index('idx_agent_active', 'agent_id', 'is_active'),         # Pour les chats d'un agent
    )
    
    # Relations
    user = relationship("User", back_populates="chats")
    agent = relationship("Agent", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan", order_by="Message.created_at")
    
    def __repr__(self):
        return f"<Chat(id={self.id}, title='{self.title}', user_id={self.user_id}, agent_id={self.agent_id})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "user_id": str(self.user_id),
            "agent_id": str(self.agent_id),
            "is_active": self.is_active,
            "is_archived": self.is_archived,
            "summary": self.summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "message_count": len(self.messages) if self.messages else 0,
        }