import hashlib
import logging
import secrets
from typing import Dict, Iterable, List, Optional, Set, Tuple

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GroupMember, Permission, PrincipalRole, Role, RolePermission, User

logger = logging.getLogger(__name__)


PERM_AGENT_CREATE = "agent:create"
PERM_AGENT_UPDATE_OWN = "agent:update:own"
PERM_AGENT_UPDATE_ANY = "agent:update:any"
PERM_AGENT_DELETE_OWN = "agent:delete:own"
PERM_AGENT_DELETE_ANY = "agent:delete:any"

PERM_ADMIN_USERS_MANAGE = "admin:users:manage"
PERM_ADMIN_DASHBOARD_VIEW = "admin:dashboard:view"

PERM_RBAC_MANAGE_ROLES = "rbac:manage_roles"
PERM_RBAC_MANAGE_GROUPS = "rbac:manage_groups"
PERM_RBAC_MANAGE_SERVICES = "rbac:manage_services"


DEFAULT_PERMISSIONS: List[Tuple[str, str]] = [
    (PERM_AGENT_CREATE, "Créer de nouveaux agents"),
    (PERM_AGENT_UPDATE_OWN, "Mettre à jour ses propres agents"),
    (PERM_AGENT_UPDATE_ANY, "Mettre à jour tous les agents"),
    (PERM_AGENT_DELETE_OWN, "Supprimer ses propres agents"),
    (PERM_AGENT_DELETE_ANY, "Supprimer tous les agents"),
    (PERM_ADMIN_USERS_MANAGE, "Gérer les utilisateurs et l'administration"),
    (PERM_ADMIN_DASHBOARD_VIEW, "Accéder au tableau de bord admin"),
    (PERM_RBAC_MANAGE_ROLES, "Gérer les rôles et permissions"),
    (PERM_RBAC_MANAGE_GROUPS, "Gérer les groupes d'utilisateurs"),
    (PERM_RBAC_MANAGE_SERVICES, "Gérer les comptes service et leurs droits"),
]

ROLE_ADMIN = "admin"
ROLE_BUILDER = "builder"
ROLE_VIEWER = "viewer"


DEFAULT_ROLES: Dict[str, List[str]] = {
    ROLE_ADMIN: [
        PERM_AGENT_CREATE,
        PERM_AGENT_UPDATE_OWN,
        PERM_AGENT_UPDATE_ANY,
        PERM_AGENT_DELETE_OWN,
        PERM_AGENT_DELETE_ANY,
        PERM_ADMIN_USERS_MANAGE,
        PERM_ADMIN_DASHBOARD_VIEW,
        PERM_RBAC_MANAGE_ROLES,
        PERM_RBAC_MANAGE_GROUPS,
        PERM_RBAC_MANAGE_SERVICES,
    ],
    ROLE_BUILDER: [
        PERM_AGENT_CREATE,
        PERM_AGENT_UPDATE_OWN,
        PERM_AGENT_DELETE_OWN,
    ],
    ROLE_VIEWER: [],
}


async def ensure_rbac_defaults(session: AsyncSession) -> None:
    """Ensure default permissions and roles exist and are consistent."""
    existing_permissions: Dict[str, Permission] = {}
    result = await session.execute(select(Permission))
    for perm in result.scalars():
        existing_permissions[perm.code] = perm

    for code, description in DEFAULT_PERMISSIONS:
        if code not in existing_permissions:
            perm = Permission(code=code, description=description)
            session.add(perm)
            existing_permissions[code] = perm

    await session.flush()

    existing_roles: Dict[str, Role] = {}
    result = await session.execute(select(Role))
    for role in result.scalars():
        existing_roles[role.name] = role

    for name, perm_codes in DEFAULT_ROLES.items():
        role = existing_roles.get(name)
        if not role:
            role = Role(name=name, description=name.capitalize(), is_system=True)
            session.add(role)
            existing_roles[name] = role

        role_permissions_query: Select[Tuple[str]] = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role.id)
        )
        result = await session.execute(role_permissions_query)
        current_codes = {code for (code,) in result.all()}

        requested_codes = set(perm_codes)
        missing_codes = requested_codes - current_codes

        if not missing_codes:
            continue

        for code in missing_codes:
            perm = existing_permissions.get(code)
            if not perm:
                continue
            link = RolePermission(role_id=role.id, permission_id=perm.id)
            session.add(link)

    await session.flush()

    builder_role = existing_roles.get(ROLE_BUILDER)
    if builder_role:
        result = await session.execute(select(User.id))
        user_ids = [user_id for (user_id,) in result.all()]

        if user_ids:
            existing_builder_links = await session.execute(
                select(PrincipalRole.principal_id).where(
                    and_(
                        PrincipalRole.principal_type == "user",
                        PrincipalRole.role_id == builder_role.id,
                        PrincipalRole.principal_id.in_(user_ids),
                    )
                )
            )
            already_builder = {pid for (pid,) in existing_builder_links.all()}

            for user_id in user_ids:
                if user_id in already_builder:
                    continue
                session.add(
                    PrincipalRole(
                        principal_type="user",
                        principal_id=user_id,
                        role_id=builder_role.id,
                    )
                )

    await session.commit()


async def _get_user_role_ids(session: AsyncSession, user: User) -> Set[str]:
    role_ids: Set[str] = set()

    direct_roles = await session.execute(
        select(PrincipalRole.role_id).where(
            and_(
                PrincipalRole.principal_type == "user",
                PrincipalRole.principal_id == user.id,
            )
        )
    )
    role_ids.update(direct_roles.scalars())

    group_ids_result = await session.execute(
        select(GroupMember.group_id).where(GroupMember.user_id == user.id)
    )
    group_ids = set(group_ids_result.scalars())

    if not group_ids:
        return role_ids

    group_roles = await session.execute(
        select(PrincipalRole.role_id).where(
            and_(
                PrincipalRole.principal_type == "group",
                PrincipalRole.principal_id.in_(group_ids),
            )
        )
    )
    role_ids.update(group_roles.scalars())
    return role_ids


async def get_user_permissions(
    session: AsyncSession,
    user: Optional[User],
) -> Set[str]:
    if not user:
        return set()

    if getattr(user, "is_admin", False):
        result = await session.execute(select(Permission.code))
        return {code for (code,) in result.all()}

    role_ids = await _get_user_role_ids(session, user)
    if not role_ids:
        return set()

    result = await session.execute(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id.in_(role_ids))
    )
    return {code for (code,) in result.all()}


async def user_has_permission(
    session: AsyncSession,
    user: Optional[User],
    permission_code: str,
) -> bool:
    if not user:
        return False

    if getattr(user, "is_admin", False):
        return True

    permissions = await get_user_permissions(session, user)
    return permission_code in permissions


async def assign_default_roles_for_user(
    session: AsyncSession,
    user: User,
) -> None:
    result = await session.execute(select(Role).where(Role.name == ROLE_BUILDER))
    builder_role = result.scalar_one_or_none()
    if not builder_role:
        logger.error("Builder role not found when assigning default roles to user %s", user.id)
        return

    existing_link = await session.execute(
        select(PrincipalRole.id).where(
            and_(
                PrincipalRole.principal_type == "user",
                PrincipalRole.principal_id == user.id,
                PrincipalRole.role_id == builder_role.id,
            )
        )
    )
    if existing_link.scalar_one_or_none():
        return

    session.add(
        PrincipalRole(
            principal_type="user",
            principal_id=user.id,
            role_id=builder_role.id,
        )
    )
    await session.flush()


def generate_service_token() -> str:
    return secrets.token_urlsafe(48)


def hash_service_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
