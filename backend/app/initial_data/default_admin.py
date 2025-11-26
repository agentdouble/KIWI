import logging
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)


def _normalize_email(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized or None


async def ensure_default_admin_user(session: AsyncSession) -> None:
    """Ensure a default admin account exists based on environment variables."""
    email = _normalize_email(settings.default_admin_email)
    trigramme = settings.default_admin_trigramme_normalized
    raw_password = settings.default_admin_password or ""
    password = raw_password.strip()

    missing = []
    if not email:
        missing.append("DEFAULT_ADMIN_EMAIL")
    if not trigramme:
        missing.append("DEFAULT_ADMIN_TRIGRAMME")
    if not password:
        missing.append("DEFAULT_ADMIN_PASSWORD")

    if missing:
        logger.info("Default admin not configured; missing %s", ", ".join(missing))
        return

    result = await session.execute(
        select(User).where(
            or_(
                User.trigramme == trigramme,
                func.lower(User.email) == email,
            )
        )
    )
    users = result.scalars().all()

    if len(users) > 1:
        logger.error(
            "Multiple users match default admin identifiers (trigramme=%s, email=%s); "
            "please resolve duplicates manually.",
            trigramme,
            email,
        )
        return

    user = users[0] if users else None

    if not user:
        user = User(
            email=email,
            trigramme=trigramme,
            is_active=True,
            must_change_password=False,
        )
        user.set_password(password)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("Created default admin account %s (%s)", trigramme, email)
        return

    updated = False

    if user.email != email:
        email_conflict = await session.execute(
            select(User.id).where(func.lower(User.email) == email, User.id != user.id)
        )
        if email_conflict.scalar_one_or_none():
            logger.error(
                "Cannot update default admin email to %s because another user already uses it",
                email,
            )
            return
        user.email = email
        updated = True

    if user.trigramme != trigramme:
        trigram_conflict = await session.execute(
            select(User.id).where(User.trigramme == trigramme, User.id != user.id)
        )
        if trigram_conflict.scalar_one_or_none():
            logger.error(
                "Cannot update default admin trigramme to %s because another user already uses it",
                trigramme,
            )
            return
        user.trigramme = trigramme
        updated = True

    if not user.is_active:
        user.is_active = True
        updated = True

    if user.must_change_password:
        user.must_change_password = False
        updated = True

    if not user.check_password(password):
        user.set_password(password)
        updated = True

    if updated:
        await session.commit()
        await session.refresh(user)
        logger.info("Updated default admin account %s (%s)", trigramme, email)
    else:
        logger.info("Default admin account %s already up-to-date", trigramme)
