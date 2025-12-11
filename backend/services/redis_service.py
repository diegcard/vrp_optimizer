"""
===========================================
Servicio de Redis - Cache y Colas
===========================================
"""

import redis.asyncio as redis
from typing import Optional, Any
from loguru import logger

from config.settings import settings


class RedisService:
    """
    Servicio de Redis para cache y colas.
    """
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._client: Optional[redis.Redis] = None
    
    async def _get_client(self) -> redis.Redis:
        """Obtener o crear cliente Redis"""
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._client
    
    async def ping(self) -> bool:
        """Verificar conexión"""
        try:
            client = await self._get_client()
            return await client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """Obtener valor"""
        client = await self._get_client()
        return await client.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: int = None
    ) -> bool:
        """Establecer valor"""
        client = await self._get_client()
        return await client.set(key, value, ex=expire)
    
    async def delete(self, key: str) -> int:
        """Eliminar clave"""
        client = await self._get_client()
        return await client.delete(key)
    
    async def close(self):
        """Cerrar conexión"""
        if self._client:
            await self._client.close()
