"""
Cache service for NOC Canvas using Redis.
"""

import json
import logging
import asyncio
from typing import Any, Optional
from .config import settings

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("Redis library not available. Caching will be disabled.")
    REDIS_AVAILABLE = False


class CacheService:
    """Redis-based cache service."""

    def __init__(self):
        self.redis: Optional[Any] = None
        self.enabled = REDIS_AVAILABLE

    async def connect(self):
        """Connect to Redis."""
        if not self.enabled:
            logger.info("Redis not available, caching disabled")
            return

        try:
            self.redis = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            await self.redis.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching will be disabled.")
            self.redis = None

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            try:
                await self.redis.aclose()
                logger.info("Disconnected from Redis cache")
            except Exception as e:
                logger.warning(f"Error disconnecting from Redis: {e}")
            finally:
                self.redis = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis:
            return None

        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        if not self.redis:
            return False

        try:
            ttl = ttl or settings.cache_ttl_seconds
            serialized_value = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis:
            return False

        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern."""
        if not self.redis:
            return 0

        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0

    def generate_key(self, service: str, endpoint: str, **kwargs) -> str:
        """Generate a cache key."""
        key_parts = [service, endpoint]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)


# Global cache instance
cache_service = CacheService()