from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

# Response DTOs
class SessionResponse(BaseModel):
    session_id: str = Field(alias="session_id")
    created_at: datetime = Field(alias="created_at")
    
    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }