from sqlalchemy import Column, String, DateTime, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import uuid
from passlib.context import CryptContext
from datetime import datetime, timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    trigramme = Column(String(3), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    must_change_password = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    agents = relationship("Agent", back_populates="user", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    favorite_agents = relationship("AgentFavorite", back_populates="user", cascade="all, delete-orphan")
    feedback_entries = relationship("FeedbackLoop", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password: str) -> None:
        self.password_hash = pwd_context.hash(password)
        self.password_changed_at = datetime.now(timezone.utc)
    
    def check_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)
    
    def __repr__(self):
        return f"<User(id={self.id}, trigramme='{self.trigramme}', email='{self.email}')>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "trigramme": self.trigramme,
            "is_active": self.is_active,
            "must_change_password": self.must_change_password,
            "password_changed_at": self.password_changed_at.isoformat() if self.password_changed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_admin(self) -> bool:
        from app.config import settings

        if not self.trigramme:
            return False
        return self.trigramme.upper() in settings.admin_trigrammes
