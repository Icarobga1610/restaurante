"""Redis caching service for the application."""

import json
from typing import Optional, Any
import redis.asyncio as redis


class CacheService:
    """Service for caching data using Redis."""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or "redis://localhost:6379/0"
        self._client: Optional[redis.Redis] = None
    
    def get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(self.redis_url)
        return self._client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        client = self.get_client()
        value = await client.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache with TTL."""
        client = self.get_client()
        await client.set(key, json.dumps(value), ex=ttl)
    
    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        client = self.get_client()
        await client.delete(key)
    
    async def clear(self) -> None:
        """Clear all cache."""
        client = self.get_client()
        await client.flushdb()


# Global cache instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service