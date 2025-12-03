import redis.asyncio as redis
import json
import logging
from typing import Optional, Any
from uuid import uuid4
from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Service de cache Redis pour améliorer les performances et la coordination."""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._connection_url = settings.redis_url

    async def connect(self):
        """Établir la connexion Redis."""
        try:
            self.redis_client = redis.from_url(
                self._connection_url,
                encoding="utf-8",
                decode_responses=True,
                socket_keepalive=True,
                health_check_interval=30,
            )
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.warning("Redis connection failed: %s. Caching will be disabled.", e)
            self.redis_client = None

    async def disconnect(self):
        """Fermer la connexion Redis."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

    async def get(self, key: str) -> Optional[Any]:
        """Récupérer une valeur du cache."""
        if not self.redis_client:
            return None

        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("Cache get error for key %s: %s", key, e)
            return None

    async def set(self, key: str, value: Any, expire_seconds: int = 3600) -> bool:
        """Stocker une valeur dans le cache."""
        if not self.redis_client:
            return False

        try:
            serialized_value = json.dumps(value, default=str)
            await self.redis_client.setex(key, expire_seconds, serialized_value)
            return True
        except Exception as e:
            logger.error("Cache set error for key %s: %s", key, e)
            return False

    async def delete(self, key: str) -> bool:
        """Supprimer une clé du cache."""
        if not self.redis_client:
            return False

        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error("Cache delete error for key %s: %s", key, e)
            return False

    async def exists(self, key: str) -> bool:
        """Vérifier si une clé existe dans le cache."""
        if not self.redis_client:
            return False

        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error("Cache exists error for key %s: %s", key, e)
            return False

    def generate_key(self, prefix: str, *args) -> str:
        """Générer une clé de cache standardisée."""
        key_parts = [prefix] + [str(arg) for arg in args if arg is not None]
        return ":".join(key_parts)

    async def acquire_lock(self, key: str, ttl_seconds: int = 60) -> Optional[str]:
        """
        Acquérir un verrou distribué.

        Retourne un token si le verrou est acquis, None si déjà verrouillé.
        Lève une erreur si Redis n'est pas disponible ou en cas d'erreur réseau.
        """
        if not self.redis_client:
            logger.error("Redis client is not available for lock %s", key)
            raise RuntimeError("Redis lock unavailable")

        token = str(uuid4())
        try:
            # SET key value NX EX ttl_seconds
            acquired = await self.redis_client.set(key, token, ex=ttl_seconds, nx=True)
            if acquired:
                logger.info("Lock acquired for key %s", key)
                return token
            logger.info("Lock already held for key %s", key)
            return None
        except Exception as e:
            logger.error("Cache lock acquire error for key %s: %s", key, e)
            raise

    async def release_lock(self, key: str, token: str) -> None:
        """
        Libérer un verrou distribué de manière sûre (check-and-del).

        Ne lève pas d'erreur fonctionnelle si le verrou n'existe plus, mais loggue les anomalies.
        """
        if not self.redis_client:
            logger.error("Redis client is not available to release lock %s", key)
            return

        # Script LUA pour ne supprimer que si le token correspond
        script = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('del', KEYS[1])
        else
            return 0
        end
        """

        try:
            await self.redis_client.eval(script, 1, key, token)
            logger.info("Lock released for key %s", key)
        except Exception as e:
            logger.error("Cache lock release error for key %s: %s", key, e)


# Instance globale du service de cache
cache_service = CacheService()
