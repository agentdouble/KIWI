from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID

# Request DTOs
class SendMessageRequest(BaseModel):
    content: str
    chat_id: str = Field(alias="chat_id")
    is_regeneration: bool = False  # Indique si c'est une régénération
    
    class Config:
        populate_by_name = True


class EditMessageRequest(BaseModel):
    content: str

# Response DTOs
class MessageResponse(BaseModel):
    id: str
    role: Literal['user', 'assistant', 'system']
    content: str
    created_at: datetime = Field(alias="created_at")
    chat_id: str = Field(alias="chat_id")
    tool_calls: Optional[list[str]] = None  # Liste des outils utilisés
    feedback: Optional[Literal['up', 'down']] = None
    is_edited: Optional[bool] = None
    user_message_id: Optional[str] = Field(default=None, alias="user_message_id")
    
    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class MessageFeedbackRequest(BaseModel):
    feedback: Literal['up', 'down']


class MessageFeedbackResponse(BaseModel):
    message_id: str
    feedback: Optional[Literal['up', 'down']] = None

    class Config:
        populate_by_name = True
