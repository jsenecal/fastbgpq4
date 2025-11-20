from functools import lru_cache

from app.bgpq4 import BGPq4Client
from app.cache import RedisCache
from app.config import settings
from app.tasks.broker import get_broker as _get_broker


@lru_cache
def get_cache() -> RedisCache:
    """Get Redis cache instance."""
    return RedisCache(settings.redis_url)


@lru_cache
def get_bgpq4_client() -> BGPq4Client:
    """Get BGPq4 client instance."""
    return BGPq4Client(
        binary_path=settings.bgpq4_binary,
        default_sources=settings.irr_sources,
        max_retries=settings.max_retries,
        retry_backoff=settings.retry_backoff_factor,
    )


@lru_cache
def get_broker():
    """Get Taskiq broker instance."""
    return _get_broker(settings.redis_url)
