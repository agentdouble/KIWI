from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base
import uuid
from datetime import datetime, timedelta

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), 
                       default=lambda: datetime.utcnow() + timedelta(hours=24))
    session_metadata = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)