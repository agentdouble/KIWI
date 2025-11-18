from sqlalchemy import Column, String, Text, DateTime, ForeignKey, CheckConstraint, Boolean, Float, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import uuid

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)
    
    # Contenu du message
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    
    # Métadonnées LLM (pour les réponses de l'assistant)
    model_used = Column(String(100))  # Modèle utilisé pour générer la réponse
    tokens_used = Column(Integer)     # Nombre de tokens utilisés
    processing_time = Column(Float)   # Temps de traitement en secondes
    temperature = Column(Float)       # Température utilisée
    
    # Statut du message
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    
    # Métadonnées supplémentaires
    message_metadata = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Contraintes et indexes pour la performance
    __table_args__ = (
        CheckConstraint(role.in_(['user', 'assistant', 'system']), name='check_role'),
        Index('idx_chat_created', 'chat_id', 'created_at'),  # Pour récupérer l'historique des messages
        Index('idx_chat_role', 'chat_id', 'role'),          # Pour filtrer par rôle dans un chat
    )
    
    # Relations
    chat = relationship("Chat", back_populates="messages")
    feedback_entries = relationship("FeedbackLoop", back_populates="message", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Message(id={self.id}, chat_id={self.chat_id}, role='{self.role}')>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "chat_id": str(self.chat_id),
            "role": self.role,
            "content": self.content,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "processing_time": self.processing_time,
            "temperature": self.temperature,
            "is_edited": self.is_edited,
            "is_deleted": self.is_deleted,
            "message_metadata": self.message_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
