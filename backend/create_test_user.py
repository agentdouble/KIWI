#!/usr/bin/env python3
"""
Script pour créer un utilisateur de test dans la base de données locale
"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.utils.auth import get_password_hash

async def create_test_user():
    async with AsyncSessionLocal() as db:
        # Vérifier si l'utilisateur existe déjà
        result = await db.execute(select(User).filter(User.email == "gjv@foyer.lu"))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"❌ L'utilisateur gjv@foyer.lu existe déjà")
            return
        
        # Créer un nouvel utilisateur
        user = User(
            email="gjv@foyer.lu",
            trigramme="GJV"
        )
        user.set_password("test123")  # Changez ce mot de passe !
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        print(f"✅ Utilisateur créé avec succès:")
        print(f"   Email: {user.email}")
        print(f"   Trigramme: {user.trigramme}")
        print(f"   Mot de passe: test123")
        print(f"   ID: {user.id}")

if __name__ == "__main__":
    asyncio.run(create_test_user())