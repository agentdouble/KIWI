from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class ChatCountPerHour(BaseModel):
    hour: datetime
    count: int


class ChatCountPerDay(BaseModel):
    day: datetime
    count: int


class ChatCountPerAgent(BaseModel):
    agent_id: Optional[UUID]
    agent_name: Optional[str]
    creator_trigramme: Optional[str]
    count: int


class UserMessagesToday(BaseModel):
    user_id: UUID
    email: Optional[str]
    trigramme: Optional[str]
    message_count: int


class DashboardStatsResponse(BaseModel):
    total_chats: int
    active_chats: int
    chats_per_hour: List[ChatCountPerHour]
    chats_per_day: List[ChatCountPerDay]
    chats_per_agent: List[ChatCountPerAgent]
    users_today: List[UserMessagesToday]


class AdminManagedUser(BaseModel):
    id: UUID
    email: str
    trigramme: str
    is_active: bool
    must_change_password: bool
    password_changed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class AdminCreateUserRequest(BaseModel):
    email: EmailStr
    trigramme: str
    temporary_password: str


class AdminResetPasswordRequest(BaseModel):
    temporary_password: str


class PermissionSummary(BaseModel):
    code: str
    description: Optional[str] = None


class RoleSummary(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    is_system: bool
    permissions: List[str]


class GroupSummary(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    is_system: bool
    member_count: int


class GroupCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class GroupDetail(GroupSummary):
    members: List[AdminManagedUser]


class ServiceAccountSummary(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool


class ServiceAccountCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class ServiceAccountTokenResponse(BaseModel):
    service_id: UUID
    token: str
