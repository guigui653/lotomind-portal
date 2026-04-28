"""Redis client manager with async connection lifecycle."""

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Manages the async Redis connection pool and provides cache operations."""

    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None

    async def connect(self) -> None:
        """Initialize the Redis connection pool."""
        self._client = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True,
        )
        logger.info("Redis connected at %s:%s", settings.REDIS_HOST, settings.REDIS_PORT)

    async def disconnect(self) -> None:
        """Close the Redis connection pool gracefully."""
        if self._client:
            await self._client.close()
            logger.info("Redis connection closed")

    async def get_cached(self, key: str) -> Any | None:
        """Retrieve a JSON-serialized value from cache."""
        if not self._client:
            return None
        value = await self._client.get(key)
        if value:
            logger.debug("Cache HIT for key: %s", key)
            return json.loads(value)
        logger.debug("Cache MISS for key: %s", key)
        return None

    async def set_cached(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a JSON-serialized value in cache with optional TTL."""
        if not self._client:
            return
        effective_ttl = ttl or settings.REDIS_CACHE_TTL
        await self._client.set(key, json.dumps(value), ex=effective_ttl)
        logger.debug("Cache SET for key: %s (TTL: %ds)", key, effective_ttl)

    async def delete_cached(self, key: str) -> None:
        """Delete a specific key from cache."""
        if not self._client:
            return
        await self._client.delete(key)
        logger.debug("Cache DELETE for key: %s", key)


redis_manager = RedisManager()
