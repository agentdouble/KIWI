import os
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
import uuid

# Configuration minimale de l'environnement pour les tests
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("LLM_MODE", os.environ.get("LLM_MODE", "local"))
os.environ.setdefault("API_URL", os.environ.get("API_URL", "https://api.mistral.ai/v1/chat/completions"))
os.environ.setdefault("API_KEY", os.environ.get("API_KEY", "test-api-key"))

from app.config import settings

# Configuration pour les tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Fixture pour l'event loop asyncio"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Fixture pour le moteur de base de données de test"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Créer les tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Nettoyer
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Fixture pour une session de base de données"""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
def test_user_id():
    """Fixture pour un ID utilisateur de test"""
    return uuid.uuid4()

@pytest.fixture
def test_agent_id():
    """Fixture pour un ID agent de test"""
    return uuid.uuid4()

@pytest.fixture
def test_chat_id():
    """Fixture pour un ID chat de test"""
    return uuid.uuid4()
