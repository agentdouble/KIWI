#!/usr/bin/env python3
"""Initialise an admin account from environment variables."""

import asyncio
import sys
from pathlib import Path
from typing import Tuple

from sqlalchemy import select

# Allow imports when executed directly from the backend folder
sys.path.append(str(Path(__file__).parent))

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.user import User


def _load_admin_credentials() -> Tuple[str, str, str]:
    email = (settings.default_admin_email or "").strip().lower()
    trigramme = (settings.default_admin_trigramme or "").strip()
    password = settings.default_admin_password or ""

    if not email or not trigramme or not password:
        raise ValueError(
            "Set DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_TRIGRAMME and DEFAULT_ADMIN_PASSWORD in backend/.env"
        )
    return email, trigramme, password


def _normalize_trigramme(value: str) -> str:
    normalized = value.strip().upper()
    if len(normalized) != 3 or not normalized.isalpha():
        raise ValueError("DEFAULT_ADMIN_TRIGRAMME must be exactly 3 letters (A-Z)")
    return normalized


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValueError("DEFAULT_ADMIN_PASSWORD must contain at least 8 characters")


def _ensure_admin_whitelisted(trigramme: str) -> None:
    if trigramme not in settings.admin_trigrammes:
        raise ValueError(
            f"Add {trigramme} to ADMIN_TRIGRAMMES to grant admin privileges to this account"
        )


async def _upsert_admin_user(email: str, trigramme: str, password: str) -> None:
    async with AsyncSessionLocal() as db:
        existing_by_email = await db.execute(select(User).filter(User.email == email))
        user = existing_by_email.scalar_one_or_none()

        if user:
            if user.trigramme != trigramme:
                raise ValueError(
                    f"Existing user {email} has trigramme {user.trigramme}, expected {trigramme}"
                )
            print(f"✅ Admin user already exists: {user.email} ({user.trigramme}) — nothing to do")
            return

        trigramme_conflict = await db.execute(select(User).filter(User.trigramme == trigramme))
        if trigramme_conflict.scalar_one_or_none():
            raise ValueError(f"Trigramme {trigramme} is already used by another user")

        user = User(
            email=email,
            trigramme=trigramme,
            is_active=True,
            must_change_password=False,
        )
        user.set_password(password)

        db.add(user)
        await db.commit()
        await db.refresh(user)

        print(f"✅ Admin user created: {user.email} ({user.trigramme})")


async def main():
    email, raw_trigramme, password = _load_admin_credentials()
    trigramme = _normalize_trigramme(raw_trigramme)
    _validate_password(password)
    _ensure_admin_whitelisted(trigramme)
    await _upsert_admin_user(email, trigramme, password)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"❌ {exc}")
        sys.exit(1)
