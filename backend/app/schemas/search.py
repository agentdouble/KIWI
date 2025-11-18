from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from app.schemas.document import EntityType


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    entity_type: EntityType
    entity_id: UUID
    top_k: int = 6
    min_score: Optional[float] = None  # 0..1 for cosine-based similarity


class SearchHit(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_name: str
    chunk_index: int
    content: str
    distance: float
    score: float
    processed_path: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    hits: List[SearchHit]

