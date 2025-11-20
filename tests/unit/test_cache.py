from unittest.mock import AsyncMock, patch

import pytest

from app.cache import RedisCache


@pytest.fixture
def mock_redis():
    with patch("app.cache.redis.from_url") as mock:
        redis_client = AsyncMock()
        mock.return_value = redis_client
        yield redis_client


@pytest.mark.asyncio
async def test_cache_get_hit(mock_redis):
    mock_redis.get.return_value = b'{"data": "test"}'
    cache = RedisCache("redis://localhost")
    result = await cache.get("test_key")
    assert result == {"data": "test"}
    mock_redis.get.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_cache_get_miss(mock_redis):
    mock_redis.get.return_value = None
    cache = RedisCache("redis://localhost")
    result = await cache.get("test_key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_set(mock_redis):
    cache = RedisCache("redis://localhost")
    await cache.set("test_key", {"data": "test"}, ttl=300)
    mock_redis.setex.assert_called_once()
    args = mock_redis.setex.call_args[0]
    assert args[0] == "test_key"
    assert args[1] == 300


@pytest.mark.asyncio
async def test_cache_generate_key():
    cache = RedisCache("redis://localhost")
    key = cache.generate_key(target="AS-HURRICANE", sources=["RIPE"], aggregate=True, format="json")
    assert "AS-HURRICANE" in key
    assert "RIPE" in key
    assert key.startswith("bgpq4:")


@pytest.mark.asyncio
async def test_cache_delete(mock_redis):
    cache = RedisCache("redis://localhost")
    await cache.delete("test_key")
    mock_redis.delete.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_cache_close(mock_redis):
    cache = RedisCache("redis://localhost")
    # Initialize client
    await cache.get_client()
    await cache.close()
    mock_redis.close.assert_called_once()


@pytest.mark.asyncio
async def test_cache_close_no_client():
    """Test close when no client has been created."""
    cache = RedisCache("redis://localhost")
    # Should not raise when client is None
    await cache.close()


@pytest.mark.asyncio
async def test_cache_get_error(mock_redis):
    """Test that cache get raises CacheError on Redis failure."""
    from app.exceptions import CacheError

    mock_redis.get.side_effect = Exception("Redis connection failed")
    cache = RedisCache("redis://localhost")
    with pytest.raises(CacheError) as exc_info:
        await cache.get("test_key")
    assert "Failed to get from cache" in str(exc_info.value)


@pytest.mark.asyncio
async def test_cache_set_error(mock_redis):
    """Test that cache set raises CacheError on Redis failure."""
    from app.exceptions import CacheError

    mock_redis.setex.side_effect = Exception("Redis connection failed")
    cache = RedisCache("redis://localhost")
    with pytest.raises(CacheError) as exc_info:
        await cache.set("test_key", {"data": "test"}, ttl=300)
    assert "Failed to set in cache" in str(exc_info.value)


@pytest.mark.asyncio
async def test_cache_delete_error(mock_redis):
    """Test that cache delete raises CacheError on Redis failure."""
    from app.exceptions import CacheError

    mock_redis.delete.side_effect = Exception("Redis connection failed")
    cache = RedisCache("redis://localhost")
    with pytest.raises(CacheError) as exc_info:
        await cache.delete("test_key")
    assert "Failed to delete from cache" in str(exc_info.value)
