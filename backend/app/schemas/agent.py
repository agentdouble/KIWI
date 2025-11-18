from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# Request DTOs
class CreateAgentRequest(BaseModel):
    name: str
    description: str
    system_prompt: str = Field(alias="system_prompt")
    avatar: Optional[str] = None
    avatar_image: Optional[str] = Field(None, alias="avatar_image")
    capabilities: List[str] = []
    category: Optional[str] = 'general'
    tags: Optional[List[str]] = []
    is_public: bool = False
    
    class Config:
        populate_by_name = True
    
    @model_validator(mode='after')
    def validate_avatar(self) -> 'CreateAgentRequest':
        if not self.avatar and not self.avatar_image:
            raise ValueError("Un avatar (emoji ou image) est obligatoire")
        return self

class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = Field(None, alias="system_prompt")
    avatar: Optional[str] = None
    avatar_image: Optional[str] = Field(None, alias="avatar_image")
    capabilities: Optional[List[str]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    
    class Config:
        populate_by_name = True

# Response DTOs
class AgentResponse(BaseModel):
    id: str
    name: str
    description: str
    system_prompt: str = Field(alias="system_prompt")
    avatar: Optional[str] = None
    avatar_image: Optional[str] = Field(None, alias="avatar_image")
    capabilities: List[str] = []
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    is_public: bool = Field(alias="is_public")
    created_by_trigramme: Optional[str] = Field(None, alias="created_by_trigramme")
    created_at: datetime = Field(alias="created_at")
    updated_at: Optional[datetime] = Field(None, alias="updated_at")
    is_default: bool = Field(alias="is_default")
    is_favorite: bool = Field(False, alias="is_favorite")
    
    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class PopularAgentResponse(AgentResponse):
    weekly_usage_count: int = Field(alias="weekly_usage_count")
    # Champs additionnels pour les cas de repli (all-time)
    usage_period: str | None = Field(default=None, alias="usage_period")
    total_usage_count: int | None = Field(default=None, alias="total_usage_count")
