from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import Agent
from app.models.chat import Chat
from app.models.message import Message
from app.models.user import User
from app.schemas.admin import (
    ChatCountPerAgent,
    ChatCountPerDay,
    ChatCountPerHour,
    DashboardStatsResponse,
    AdminManagedUser,
    UserMessagesToday,
)
from app.utils.auth import get_current_admin_user

router = APIRouter(tags=["admin"])


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """Retourne les statistiques globales pour le tableau de bord administrateur."""
    now = datetime.now(timezone.utc)
    last_24_hours = now - timedelta(hours=24)
    last_30_days = now - timedelta(days=30)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Comptage global des chats
    total_chats_result = await db.execute(select(func.count(Chat.id)))
    total_chats = total_chats_result.scalar() or 0

    active_chats_result = await db.execute(
        select(func.count(Chat.id)).where(Chat.is_active == True)  # noqa: E712
    )
    active_chats = active_chats_result.scalar() or 0

    # Chats par heure (24 dernières heures)
    hour_trunc = func.date_trunc("hour", Chat.created_at).label("hour")
    hourly_stmt = (
        select(hour_trunc, func.count(Chat.id).label("count"))
        .where(Chat.created_at >= last_24_hours)
        .group_by(hour_trunc)
        .order_by(hour_trunc.asc())
    )
    hourly_result = await db.execute(hourly_stmt)
    chats_per_hour: List[ChatCountPerHour] = [
        ChatCountPerHour(hour=row.hour, count=int(row.count)) for row in hourly_result.all()
    ]

    # Chats par jour (30 derniers jours)
    day_trunc = func.date_trunc("day", Chat.created_at).label("day")
    daily_stmt = (
        select(day_trunc, func.count(Chat.id).label("count"))
        .where(Chat.created_at >= last_30_days)
        .group_by(day_trunc)
        .order_by(day_trunc.asc())
    )
    daily_result = await db.execute(daily_stmt)
    chats_per_day: List[ChatCountPerDay] = [
        ChatCountPerDay(day=row.day, count=int(row.count)) for row in daily_result.all()
    ]

    # Chats par agent (30 derniers jours)
    agent_stmt = (
        select(
            Chat.agent_id.label("agent_id"),
            Agent.name.label("agent_name"),
            User.trigramme.label("creator_trigramme"),
            func.count(Chat.id).label("count"),
        )
        .outerjoin(Agent, Chat.agent_id == Agent.id)
        .outerjoin(User, Agent.user_id == User.id)
        .where(Chat.created_at >= last_30_days)
        .group_by(Chat.agent_id, Agent.name, User.trigramme)
        .order_by(func.count(Chat.id).desc())
    )
    agent_result = await db.execute(agent_stmt)
    chats_per_agent: List[ChatCountPerAgent] = [
        ChatCountPerAgent(
            agent_id=row.agent_id,
            agent_name=row.agent_name,
            creator_trigramme=row.creator_trigramme,
            count=int(row.count),
        )
        for row in agent_result.all()
        if row.agent_id is not None
    ]

    # Utilisateurs actifs du jour (messages envoyés aujourd'hui)
    user_stmt = (
        select(
            User.id.label("user_id"),
            User.email.label("email"),
            User.trigramme.label("trigramme"),
            func.count(Message.id).label("message_count"),
        )
        .join(Chat, Chat.user_id == User.id)
        .join(
            Message,
            and_(
                Message.chat_id == Chat.id,
                Message.role == "user",
                Message.created_at >= today_start,
                Message.created_at <= now,
            ),
        )
        .group_by(User.id)
        .order_by(func.count(Message.id).desc())
    )
    user_result = await db.execute(user_stmt)
    users_today = [
        UserMessagesToday(
            user_id=row.user_id,
            email=row.email,
            trigramme=row.trigramme,
            message_count=int(row.message_count),
        )
        for row in user_result.all()
    ]

    return DashboardStatsResponse(
        total_chats=int(total_chats),
        active_chats=int(active_chats),
        chats_per_hour=chats_per_hour,
        chats_per_day=chats_per_day,
        chats_per_agent=chats_per_agent,
        users_today=users_today,
    )


@router.get("/users", response_model=List[AdminManagedUser])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """Retourne la liste des utilisateurs pour l'administration."""
    stmt = select(User).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    users = result.scalars().all()

    return [
        AdminManagedUser(
            id=user.id,
            email=user.email,
            trigramme=user.trigramme,
            is_active=bool(user.is_active),
            created_at=user.created_at,
        )
        for user in users
    ]


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """Supprime un utilisateur et toutes ses ressources associées."""
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer votre propre compte administrateur.",
        )

    user = await db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    await db.delete(user)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
