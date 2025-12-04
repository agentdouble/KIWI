import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

DEFAULT_ADMIN_PASSWORD = "admin"


def _get_admin_trigrammes() -> List[str]:
    """Retourne la liste normalisée des trigrammes admin."""
    return settings.admin_trigrammes


async def ensure_initial_admin(session: AsyncSession) -> None:
    """
    Garantit qu'au moins un compte admin existe en base.

    Règles :
    - Si un utilisateur avec un trigramme présent dans ADMIN_TRIGRAMMES existe, ne rien faire.
    - Sinon, création d'un utilisateur par défaut :
      - email : DEFAULT_ADMIN_EMAIL
      - trigramme : premier trigramme de ADMIN_TRIGRAMMES s'il est défini, sinon DEFAULT_ADMIN_TRIGRAM
      - mot de passe : DEFAULT_ADMIN_PASSWORD
      - must_change_password = True pour forcer le changement à la première connexion.
    """
    admin_trigrammes = _get_admin_trigrammes()

    if not admin_trigrammes:
        logger.warning(
            "ADMIN_TRIGRAMMES is empty; no admin accounts will be auto-created."
        )
        return

    for trigram in admin_trigrammes:
        normalized = (trigram or "").strip().upper()
        if not normalized:
            continue

        result = await session.execute(
            select(User).where(User.trigramme == normalized).limit(1)
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            continue

        email = f"{normalized.lower()}@localhost"

        user = User(
            email=email,
            trigramme=normalized,
            is_active=True,
        )
        user.set_password(DEFAULT_ADMIN_PASSWORD)
        user.must_change_password = True

        session.add(user)

        try:
            await session.commit()
        except IntegrityError:
            # Cas de contention multi-processus : un autre worker a créé l'admin
            await session.rollback()
            logger.info(
                "Admin user creation raced for trigram '%s'; assuming admin now exists.",
                normalized,
            )
            continue

        await session.refresh(user)

        logger.warning(
            "Created initial admin user with trigram '%s' and email '%s'. "
            "Default password is '%s' and must be changed at first login.",
            normalized,
            email,
            DEFAULT_ADMIN_PASSWORD,
        )
