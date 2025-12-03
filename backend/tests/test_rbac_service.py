import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, GroupMember, Permission, PrincipalRole, Role, RolePermission
from app.models.user import User
from app.services.rbac_service import (
    PERM_ADMIN_USERS_MANAGE,
    PERM_AGENT_CREATE,
    ROLE_BUILDER,
    assign_default_roles_for_user,
    ensure_rbac_defaults,
    user_has_permission,
)


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


async def _with_session(coro):
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        def _create_tables(sync_conn):
            Base.metadata.create_all(
                bind=sync_conn,
                tables=[
                    User.__table__,
                    Role.__table__,
                    RolePermission.__table__,
                    Permission.__table__,
                    PrincipalRole.__table__,
                    GroupMember.__table__,
                ],
            )

        await conn.run_sync(_create_tables)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await coro(session)

    await engine.dispose()


def test_ensure_rbac_defaults_creates_roles_and_permissions():
    async def _test(session: AsyncSession):
        await ensure_rbac_defaults(session)

        perms = await session.execute(select(Permission.code))
        codes = {code for (code,) in perms.all()}
        assert PERM_AGENT_CREATE in codes
        assert PERM_ADMIN_USERS_MANAGE in codes

        roles = await session.execute(select(Role.name))
        role_names = {name for (name,) in roles.all()}
        assert ROLE_BUILDER in role_names

    asyncio.run(_with_session(_test))


def test_assign_default_roles_for_user_grants_builder_role():
    async def _test(session: AsyncSession):
        await ensure_rbac_defaults(session)

        user = User(email="test@example.com", trigramme="TST", is_active=True)
        user.set_password("password-secure")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        await assign_default_roles_for_user(session, user)

        builder_role = (
            await session.execute(select(Role).where(Role.name == ROLE_BUILDER))
        ).scalar_one()

        links = await session.execute(
            select(PrincipalRole).where(
                PrincipalRole.principal_type == "user",
                PrincipalRole.principal_id == user.id,
                PrincipalRole.role_id == builder_role.id,
            )
        )
        assert links.scalar_one_or_none() is not None

    asyncio.run(_with_session(_test))


def test_user_has_permission_for_builder_role():
    async def _test(session: AsyncSession):
        await ensure_rbac_defaults(session)

        user = User(email="builder@example.com", trigramme="BLD", is_active=True)
        user.set_password("password-secure")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        await assign_default_roles_for_user(session, user)

        assert await user_has_permission(session, user, PERM_AGENT_CREATE)
        assert not await user_has_permission(session, user, PERM_ADMIN_USERS_MANAGE)

    asyncio.run(_with_session(_test))
