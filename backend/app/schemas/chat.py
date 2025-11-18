from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.schemas.message import MessageResponse

# Request DTOs
class CreateChatRequest(BaseModel):
    title: Optional[str] = None
    agent_id: Optional[str] = Field(None, alias="agent_id")
    
    class Config:
        populate_by_name = True

# Response DTOs
class ChatResponse(BaseModel):
    id: str
    title: str
    messages: List[MessageResponse] = []
    created_at: datetime = Field(alias="created_at")
    updated_at: Optional[datetime] = Field(None, alias="updated_at")
    agent_id: Optional[str] = Field(None, alias="agent_id")
    session_id: Optional[str] = Field(None, alias="session_id")
    
    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }