import redis.asyncio as redis
import json
import logging
from typing import Optional, Any, Union
from app.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    """Service de cache Redis pour améliorer les performances"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._connection_url = settings.redis_url
    
    async def connect(self):
        """Établir la connexion Redis"""
        try:
            self.redis_client = redis.from_url(
                self._connection_url,
                encoding="utf-8",
                decode_responses=True,
                socket_keepalive=True,
                health_check_interval=30
            )
            # Test de la connexion
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching will be disabled.")
            self.redis_client = None
    
    async def disconnect(self):
        """Fermer la connexion Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Récupérer une valeur du cache"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire_seconds: int = 3600) -> bool:
        """Stocker une valeur dans le cache"""
        if not self.redis_client:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            await self.redis_client.setex(key, expire_seconds, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Supprimer une clé du cache"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Vérifier si une clé existe dans le cache"""
        if not self.redis_client:
            return False
        
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def generate_key(self, prefix: str, *args) -> str:
        """Générer une clé de cache standardisée"""
        key_parts = [prefix] + [str(arg) for arg in args if arg is not None]
        return ":".join(key_parts)

# Instance globale du service de cache
cache_service = CacheService()