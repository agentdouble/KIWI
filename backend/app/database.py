from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Créer l'engine async
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base pour les modèles
Base = declarative_base()

# Dependency pour obtenir une session DB
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()