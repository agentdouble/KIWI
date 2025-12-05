from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

import logging
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    Agent,
    Chat,
    FeedbackLoop,
    Group,
    GroupMember,
    Message,
    Permission,
    PrincipalRole,
    Role,
    RolePermission,
    ServiceAccount,
    ServiceToken,
    User,
)
from app.schemas.admin import (
    ChatCountPerAgent,
    ChatCountPerDay,
    ChatCountPerHour,
    DashboardStatsResponse,
    AdminFeedbackSummary,
    AdminManagedUser,
    UserMessagesToday,
    AdminCreateUserRequest,
    AdminResetPasswordRequest,
    GroupCreateRequest,
    GroupDetail,
    GroupSummary,
    PermissionSummary,
    RoleSummary,
    RoleCreateRequest,
    RoleUpdateRequest,
    ServiceAccountCreateRequest,
    ServiceAccountSummary,
    ServiceAccountTokenResponse,
)
from app.schemas.chat import ChatResponse
from app.schemas.message import MessageResponse
from app.utils.auth import get_current_admin_user
from app.services.rbac_service import (
    PERM_RBAC_MANAGE_GROUPS,
    PERM_RBAC_MANAGE_ROLES,
    PERM_RBAC_MANAGE_SERVICES,
    assign_default_roles_for_user,
    generate_service_token,
    hash_service_token,
    user_has_permission,
)

router = APIRouter(tags=["admin"])
logger = logging.getLogger(__name__)


def _serialize_admin_user(user: User) -> AdminManagedUser:
    return AdminManagedUser(
        id=user.id,
        email=user.email,
        trigramme=user.trigramme,
        is_active=bool(user.is_active),
        must_change_password=bool(user.must_change_password),
        password_changed_at=user.password_changed_at,
        created_at=user.created_at,
    )


def _validate_trigramme(value: str) -> str:
    normalized = value.strip().upper()
    if len(normalized) != 3 or not normalized.isalpha():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le trigramme doit contenir exactement 3 lettres.",
        )
    return normalized


def _validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe temporaire doit contenir au moins 8 caractères.",
        )


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


@router.get("/feedback", response_model=List[AdminFeedbackSummary])
async def list_feedback_entries(
    feedback_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """Liste les feedbacks sur les messages de l'assistant pour analyse par les administrateurs."""
    type_filter = feedback_type.lower() if feedback_type else None

    stmt = (
        select(
            FeedbackLoop.id.label("feedback_id"),
            FeedbackLoop.feedback_type.label("feedback_type"),
            FeedbackLoop.created_at.label("feedback_created_at"),
            FeedbackLoop.user_id.label("user_id"),
            User.trigramme.label("user_trigramme"),
            User.email.label("user_email"),
            Message.id.label("message_id"),
            Message.content.label("message_content"),
            Message.created_at.label("message_created_at"),
            Chat.id.label("chat_id"),
            Chat.title.label("chat_title"),
            Agent.id.label("agent_id"),
            Agent.name.label("agent_name"),
        )
        .join(Message, FeedbackLoop.message_id == Message.id)
        .join(Chat, Message.chat_id == Chat.id)
        .join(User, FeedbackLoop.user_id == User.id)
        .outerjoin(Agent, Chat.agent_id == Agent.id)
        .where(Message.role == "assistant")
    )

    if type_filter in {"up", "down"}:
        stmt = stmt.where(FeedbackLoop.feedback_type == type_filter)

    stmt = stmt.order_by(FeedbackLoop.created_at.desc())
    result = await db.execute(stmt)
    rows = result.all()

    entries: List[AdminFeedbackSummary] = []
    for row in rows:
        entries.append(
            AdminFeedbackSummary(
                id=row.feedback_id,
                feedback_type=row.feedback_type,
                created_at=row.feedback_created_at,
                user_id=row.user_id,
                user_trigramme=row.user_trigramme,
                user_email=row.user_email,
                chat_id=row.chat_id,
                chat_title=row.chat_title,
                agent_id=row.agent_id,
                agent_name=row.agent_name,
                message_id=row.message_id,
                message_created_at=row.message_created_at,
                message_content=row.message_content,
            )
        )

    logger.info(
        "Admin %s listed %d feedback entries (type=%s)",
        current_admin.trigramme,
        len(entries),
        type_filter or "all",
    )
    return entries


@router.get("/feedback/{feedback_id}/chat", response_model=ChatResponse)
async def get_feedback_chat(
    feedback_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """Retourne la conversation associée à un feedback donné (👍/👎)."""
    feedback = await db.get(FeedbackLoop, feedback_id)
    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback introuvable.")

    chat_result = await db.execute(
        select(Chat)
        .join(Message, Message.chat_id == Chat.id)
        .where(Message.id == feedback.message_id)
        .options(selectinload(Chat.messages).selectinload(Message.feedback_entries))
    )
    chat = chat_result.scalar_one_or_none()

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat introuvable pour ce feedback.",
        )

    feedback_user_id = feedback.user_id

    logger.info(
        "Admin %s accessed chat %s for feedback %s",
        current_admin.trigramme,
        chat.id,
        feedback.id,
    )

    return ChatResponse(
        id=str(chat.id),
        title=chat.title,
        messages=[
            MessageResponse(
                id=str(msg.id),
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                chat_id=str(msg.chat_id),
                tool_calls=None,
                feedback=next(
                    (
                        entry.feedback_type
                        for entry in msg.feedback_entries
                        if entry.user_id == feedback_user_id
                    ),
                    None,
                ),
                is_edited=msg.is_edited,
                user_message_id=None,
            )
            for msg in sorted(chat.messages, key=lambda m: m.created_at)
        ],
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        agent_id=str(chat.agent_id) if chat.agent_id else None,
        session_id=None,
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

    return [_serialize_admin_user(user) for user in users]


@router.post("/users", response_model=AdminManagedUser, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: AdminCreateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """Crée un nouvel utilisateur (réservé aux administrateurs)."""
    trigramme = _validate_trigramme(payload.trigramme)
    _validate_password_strength(payload.temporary_password)

    existing_email = await db.execute(select(User).filter(User.email == payload.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur existe déjà avec cet email.",
        )

    existing_trigramme = await db.execute(select(User).filter(User.trigramme == trigramme))
    if existing_trigramme.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce trigramme est déjà utilisé.",
        )

    user = User(
        email=payload.email,
        trigramme=trigramme,
        is_active=True,
        must_change_password=True,
    )
    user.set_password(payload.temporary_password)

    db.add(user)
    await db.commit()
    await db.refresh(user)

    await assign_default_roles_for_user(db, user)
    await db.commit()

    logger.info("Admin %s created user %s", current_admin.trigramme, user.trigramme)
    return _serialize_admin_user(user)


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

    logger.info("Admin %s deleted user %s", current_admin.trigramme, user.trigramme)
    await db.delete(user)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/users/{user_id}/reset-password", response_model=AdminManagedUser)
async def reset_user_password(
    user_id: UUID,
    payload: AdminResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """Réinitialise le mot de passe d'un utilisateur et force le changement à la prochaine connexion."""
    _validate_password_strength(payload.temporary_password)

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    user.set_password(payload.temporary_password)
    user.must_change_password = True

    await db.commit()
    await db.refresh(user)

    logger.info("Admin %s reset password for user %s", current_admin.trigramme, user.trigramme)
    return _serialize_admin_user(user)


@router.get("/permissions", response_model=List[PermissionSummary])
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(select(Permission).order_by(Permission.code.asc()))
    permissions = result.scalars().all()
    return [
        PermissionSummary(code=perm.code, description=perm.description)
        for perm in permissions
    ]


@router.get("/roles", response_model=List[RoleSummary])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    roles_result = await db.execute(select(Role).order_by(Role.name.asc()))
    roles = roles_result.scalars().all()

    summaries: List[RoleSummary] = []
    for role in roles:
        perm_result = await db.execute(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role.id)
        )
        perm_codes = {code for (code,) in perm_result.all()}
        summaries.append(
            RoleSummary(
                id=role.id,
                name=role.name,
                description=role.description,
                is_system=bool(role.is_system),
                permissions=sorted(perm_codes),
            )
        )
    return summaries


@router.post("/roles", response_model=RoleSummary, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    if not await user_has_permission(db, current_admin, PERM_RBAC_MANAGE_ROLES):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="RBAC role management not allowed")

    existing = await db.execute(select(Role).where(Role.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un rôle existe déjà avec ce nom.",
        )

    role = Role(
        name=payload.name,
        description=payload.description,
        is_system=False,
    )
    db.add(role)
    await db.flush()

    if payload.permissions:
        perm_rows = await db.execute(
            select(Permission).where(Permission.code.in_(set(payload.permissions)))
        )
        perms = perm_rows.scalars().all()
        for perm in perms:
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    await db.commit()
    await db.refresh(role)

    perm_codes_result = await db.execute(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role.id)
    )
    perm_codes = sorted({code for (code,) in perm_codes_result.all()})

    return RoleSummary(
        id=role.id,
        name=role.name,
        description=role.description,
        is_system=bool(role.is_system),
        permissions=perm_codes,
    )


@router.patch("/roles/{role_id}", response_model=RoleSummary)
async def update_role(
    role_id: UUID,
    payload: RoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    if not await user_has_permission(db, current_admin, PERM_RBAC_MANAGE_ROLES):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="RBAC role management not allowed")

    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle introuvable.")

    if payload.name and payload.name != role.name:
        if role.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le nom des rôles système ne peut pas être modifié.",
            )
        existing = await db.execute(select(Role).where(Role.name == payload.name))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un rôle existe déjà avec ce nom.",
            )
        role.name = payload.name

    if payload.description is not None:
        role.description = payload.description

    if payload.permissions is not None:
        await db.execute(
            delete(RolePermission).where(RolePermission.role_id == role.id)
        )
        if payload.permissions:
            perm_rows = await db.execute(
                select(Permission).where(Permission.code.in_(set(payload.permissions)))
            )
            perms = perm_rows.scalars().all()
            for perm in perms:
                db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    await db.commit()
    await db.refresh(role)

    perm_codes_result = await db.execute(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role.id)
    )
    perm_codes = sorted({code for (code,) in perm_codes_result.all()})

    return RoleSummary(
        id=role.id,
        name=role.name,
        description=role.description,
        is_system=bool(role.is_system),
        permissions=perm_codes,
    )


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    if not await user_has_permission(db, current_admin, PERM_RBAC_MANAGE_ROLES):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="RBAC role management not allowed")

    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle introuvable.")

    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Les rôles système ne peuvent pas être supprimés.",
        )

    await db.delete(role)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users/{user_id}/roles", response_model=List[RoleSummary])
async def list_user_roles(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    direct_roles_result = await db.execute(
        select(Role)
        .join(PrincipalRole, PrincipalRole.role_id == Role.id)
        .where(
            PrincipalRole.principal_type == "user",
            PrincipalRole.principal_id == user.id,
        )
        .order_by(Role.name.asc())
    )
    roles = direct_roles_result.scalars().all()

    summaries: List[RoleSummary] = []
    for role in roles:
        perm_result = await db.execute(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role.id)
        )
        perm_codes = {code for (code,) in perm_result.all()}
        summaries.append(
            RoleSummary(
                id=role.id,
                name=role.name,
                description=role.description,
                is_system=bool(role.is_system),
                permissions=sorted(perm_codes),
            )
        )
    return summaries


@router.post("/users/{user_id}/roles/{role_name}", response_model=RoleSummary)
async def assign_role_to_user(
    user_id: UUID,
    role_name: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    if not await user_has_permission(db, current_admin, PERM_RBAC_MANAGE_ROLES):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="RBAC role management not allowed")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    role_result = await db.execute(select(Role).where(Role.name == role_name))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle introuvable.")

    link_result = await db.execute(
        select(PrincipalRole).where(
            PrincipalRole.principal_type == "user",
            PrincipalRole.principal_id == user.id,
            PrincipalRole.role_id == role.id,
        )
    )
    link = link_result.scalar_one_or_none()
    if not link:
        db.add(
            PrincipalRole(
                principal_type="user",
                principal_id=user.id,
                role_id=role.id,
            )
        )
        await db.commit()

    perm_result = await db.execute(
        select(Permission.code)
        .join(Role, Role.permissions)
        .where(Role.id == role.id)
    )
    perm_codes = {code for (code,) in perm_result.all()}
    return RoleSummary(
        id=role.id,
        name=role.name,
        description=role.description,
        is_system=bool(role.is_system),
        permissions=sorted(perm_codes),
    )


@router.delete("/users/{user_id}/roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(
    user_id: UUID,
    role_name: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    if not await user_has_permission(db, current_admin, PERM_RBAC_MANAGE_ROLES):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="RBAC role management not allowed")

    role_result = await db.execute(select(Role).where(Role.name == role_name))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle introuvable.")

    link_result = await db.execute(
        select(PrincipalRole).where(
            PrincipalRole.principal_type == "user",
            PrincipalRole.principal_id == user_id,
            PrincipalRole.role_id == role.id,
        )
    )
    link = link_result.scalar_one_or_none()
    if link:
        await db.delete(link)
        await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/groups", response_model=List[GroupSummary])
async def list_groups(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    stmt = (
        select(
            Group,
            func.count(GroupMember.id).label("member_count"),
        )
        .outerjoin(GroupMember, GroupMember.group_id == Group.id)
        .group_by(Group.id)
        .order_by(Group.name.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        GroupSummary(
            id=group.id,
            name=group.name,
            description=group.description,
            is_system=bool(group.is_system),
            member_count=int(member_count or 0),
        )
        for group, member_count in rows
    ]


@router.post("/groups", response_model=GroupSummary, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: GroupCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    if not await user_has_permission(db, current_admin, PERM_RBAC_MANAGE_GROUPS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Group management not allowed")

    existing = await db.execute(select(Group).where(Group.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Un groupe existe déjà avec ce nom.")

    group = Group(
        name=payload.name,
        description=payload.description,
        is_system=False,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)

    return GroupSummary(
        id=group.id,
        name=group.name,
        description=group.description,
        is_system=bool(group.is_system),
        member_count=0,
    )


@router.get("/groups/{group_id}", response_model=GroupDetail)
async def get_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable.")

    member_stmt = (
        select(User)
        .join(GroupMember, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == group.id)
        .order_by(User.trigramme.asc())
    )
    members_result = await db.execute(member_stmt)
    members = members_result.scalars().all()

    return GroupDetail(
        id=group.id,
        name=group.name,
        description=group.description,
        is_system=bool(group.is_system),
        member_count=len(members),
        members=[_serialize_admin_user(user) for user in members],
    )


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    if not await user_has_permission(db, current_admin, PERM_RBAC_MANAGE_GROUPS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Group management not allowed")

    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable.")

    if group.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Les groupes système ne peuvent pas être supprimés.",
        )

    await db.delete(group)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/groups/{group_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_user_to_group(
    group_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    if not await user_has_permission(db, current_admin, PERM_RBAC_MANAGE_GROUPS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Group management not allowed")

    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable.")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    existing = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group.id,
            GroupMember.user_id == user.id,
        )
    )
    if not existing.scalar_one_or_none():
        db.add(GroupMember(group_id=group.id, user_id=user.id))
        await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/groups/{group_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_from_group(
    group_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    if not await user_has_permission(db, current_admin, PERM_RBAC_MANAGE_GROUPS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Group management not allowed")

    membership_result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )
    membership = membership_result.scalar_one_or_none()
    if membership:
        await db.delete(membership)
        await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/groups/{group_id}/roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
async def assign_role_to_group(
    group_id: UUID,
    role_name: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    if not await user_has_permission(db, current_admin, PERM_RBAC_MANAGE_ROLES):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="RBAC role management not allowed")

    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable.")

    role_result = await db.execute(select(Role).where(Role.name == role_name))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle introuvable.")

    existing = await db.execute(
        select(PrincipalRole).where(
            PrincipalRole.principal_type == "group",
            PrincipalRole.principal_id == group.id,
            PrincipalRole.role_id == role.id,
        )
    )
    if not existing.scalar_one_or_none():
        db.add(
            PrincipalRole(
                principal_type="group",
                principal_id=group.id,
                role_id=role.id,
            )
        )
        await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/groups/{group_id}/roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_group(
    group_id: UUID,
    role_name: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    if not await user_has_permission(db, current_admin, PERM_RBAC_MANAGE_ROLES):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="RBAC role management not allowed")

    role_result = await db.execute(select(Role).where(Role.name == role_name))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle introuvable.")

    existing = await db.execute(
        select(PrincipalRole).where(
            PrincipalRole.principal_type == "group",
            PrincipalRole.principal_id == group_id,
            PrincipalRole.role_id == role.id,
        )
    )
    link = existing.scalar_one_or_none()
    if link:
        await db.delete(link)
        await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/services", response_model=List[ServiceAccountSummary])
async def list_service_accounts(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(select(ServiceAccount).order_by(ServiceAccount.name.asc()))
    services = result.scalars().all()
    return [
        ServiceAccountSummary(
            id=service.id,
            name=service.name,
            description=service.description,
            is_active=bool(service.is_active),
        )
        for service in services
    ]


@router.post("/services", response_model=ServiceAccountTokenResponse, status_code=status.HTTP_201_CREATED)
async def create_service_account(
    payload: ServiceAccountCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    if not await user_has_permission(db, current_admin, PERM_RBAC_MANAGE_SERVICES):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Service management not allowed")

    existing = await db.execute(select(ServiceAccount).where(ServiceAccount.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Un service existe déjà avec ce nom.")

    service = ServiceAccount(
        name=payload.name,
        description=payload.description,
        is_active=True,
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)

    token_value = generate_service_token()
    token_hash = hash_service_token(token_value)

    token = ServiceToken(
        service_id=service.id,
        token_hash=token_hash,
        label="default",
        is_revoked=False,
    )
    db.add(token)
    await db.commit()

    return ServiceAccountTokenResponse(service_id=service.id, token=token_value)
