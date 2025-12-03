from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

import logging
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    Agent,
    Chat,
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
    AdminManagedUser,
    UserMessagesToday,
    AdminCreateUserRequest,
    AdminResetPasswordRequest,
    GroupCreateRequest,
    GroupDetail,
    GroupSummary,
    PermissionSummary,
    RoleSummary,
    ServiceAccountCreateRequest,
    ServiceAccountSummary,
    ServiceAccountTokenResponse,
)
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
