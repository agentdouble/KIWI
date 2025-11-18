from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    trigramme: str
    password: str


class UserLogin(BaseModel):
    identifier: str  # Peut être email ou trigramme
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    trigramme: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[UUID] = None
