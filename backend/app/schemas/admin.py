from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


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
    created_at: Optional[datetime] = None
