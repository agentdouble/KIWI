from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, CheckConstraint, Index, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates
from app.models.base import Base
import uuid
from datetime import datetime
import enum


class EntityType(str, enum.Enum):
    AGENT = "AGENT"
    CHAT = "CHAT"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value = value.upper()
            for member in cls:
                if member.value == value:
                    return member
        return None

    @property
    def slug(self) -> str:
        return self.value.lower()


class ProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value = value.upper()
            for member in cls:
                if member.value == value:
                    return member
        return None

    @property
    def slug(self) -> str:
        return self.value.lower()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(Text, nullable=False)
    processed_path = Column(Text)
    entity_type = Column(
        Enum(
            EntityType,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            name="entitytype"
        ),
        nullable=False
    )
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    processed_at = Column(DateTime(timezone=True))
    processing_status = Column(
        Enum(
            ProcessingStatus,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            name="processingstatus"
        ),
        default=ProcessingStatus.PENDING,
        nullable=False
    )
    processing_error = Column(Text)
    document_metadata = Column(JSONB, default={})
    
    # Contraintes et indexes pour la performance
    __table_args__ = (
        CheckConstraint(file_size > 0, name='check_positive_file_size'),
        Index('idx_entity', 'entity_type', 'entity_id'),    # Pour récupérer documents par entité
        Index('idx_entity_processed', 'entity_type', 'entity_id', 'processed_path'),  # Documents traités
    )
    
    # Relations dynamiques selon entity_type
    @property
    def agent(self):
        if self.entity_type == EntityType.AGENT:
            from app.models.agent import Agent
            return self.query.session.query(Agent).filter_by(id=self.entity_id).first()
        return None
    
    @property
    def chat(self):
        if self.entity_type == EntityType.CHAT:
            from app.models.chat import Chat
            return self.query.session.query(Chat).filter_by(id=self.entity_id).first()
        return None

    @validates("entity_type")
    def _validate_entity_type(self, key, value):
        if isinstance(value, str):
            return EntityType(value)
        if isinstance(value, EntityType):
            return value
        raise ValueError("entity_type must be a string or EntityType")

    @validates("processing_status")
    def _validate_processing_status(self, key, value):
        if isinstance(value, str):
            return ProcessingStatus(value)
        if isinstance(value, ProcessingStatus):
            return value
        raise ValueError("processing_status must be a string or ProcessingStatus")
