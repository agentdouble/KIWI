import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.config import settings

async def clean_empty_messages():
    # Créer la connexion à la base de données
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Supprimer les messages vides ou avec seulement des espaces
        result = await session.execute(
            text("DELETE FROM messages WHERE content IS NULL OR TRIM(content) = ''")
        )
        await session.commit()
        print(f"Supprimé {result.rowcount} messages vides")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(clean_empty_messages())
