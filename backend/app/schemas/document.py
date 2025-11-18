from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.document import EntityType, ProcessingStatus
from pydantic import field_validator, field_serializer
from uuid import UUID

class DocumentBase(BaseModel):
    name: str = Field(..., description="Nom du document")
    document_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class DocumentCreate(DocumentBase):
    pass

class DocumentUpload(BaseModel):
    entity_type: EntityType
    entity_id: UUID

class DocumentResponse(DocumentBase):
    id: UUID
    original_filename: str
    file_type: str
    file_size: int
    storage_path: str
    processed_path: Optional[str] = None
    entity_type: EntityType
    entity_id: UUID
    uploaded_by: Optional[UUID] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_error: Optional[str] = None
    document_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True

    @field_validator('entity_type', mode='before')
    @classmethod
    def _normalize_entity_type(cls, value):
        if isinstance(value, EntityType):
            return value
        if isinstance(value, str):
            return EntityType(value)
        return value

    @field_validator('processing_status', mode='before')
    @classmethod
    def _normalize_processing_status(cls, value):
        if isinstance(value, ProcessingStatus):
            return value
        if isinstance(value, str):
            return ProcessingStatus(value)
        return value

    @field_serializer('entity_type')
    def _serialize_entity_type(self, value: EntityType) -> str:
        return value.slug

    @field_serializer('processing_status')
    def _serialize_processing_status(self, value: ProcessingStatus) -> str:
        return value.slug

class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int

class DocumentContentResponse(BaseModel):
    id: UUID
    name: str
    content: str
    file_type: str
    processed: bool
