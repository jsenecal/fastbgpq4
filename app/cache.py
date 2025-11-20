import json
from typing import Any

import redis.asyncio as redis

from app.exceptions import CacheError


class RedisCache:
    """Redis cache wrapper with JSON serialization."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client = None

    async def get_client(self):
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=False)
        return self._client

    async def get(self, key: str) -> dict[str, Any] | None:
        """Get value from cache."""
        try:
            client = await self.get_client()
            value = await client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            raise CacheError(f"Failed to get from cache: {e}")

    async def set(self, key: str, value: dict[str, Any], ttl: int):
        """Set value in cache with TTL."""
        try:
            client = await self.get_client()
            serialized = json.dumps(value)
            await client.setex(key, ttl, serialized)
        except Exception as e:
            raise CacheError(f"Failed to set in cache: {e}")

    async def delete(self, key: str):
        """Delete key from cache."""
        try:
            client = await self.get_client()
            await client.delete(key)
        except Exception as e:
            raise CacheError(f"Failed to delete from cache: {e}")

    def generate_key(
        self,
        target: str,
        sources: list[str] | None = None,
        aggregate: bool = False,
        min_masklen: int | None = None,
        max_masklen: int | None = None,
        format: str = "json",
    ) -> str:
        """Generate cache key from query parameters."""
        key_parts = [
            "bgpq4",
            target,
            ",".join(sorted(sources)) if sources else "default",
            str(aggregate),
            str(min_masklen) if min_masklen else "none",
            str(max_masklen) if max_masklen else "none",
            format,
        ]
        return ":".join(key_parts)

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
