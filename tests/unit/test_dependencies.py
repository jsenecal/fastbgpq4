from unittest.mock import patch

import pytest

from app.api.dependencies import get_bgpq4_client, get_broker, get_cache


@pytest.mark.asyncio
async def test_get_cache():
    with patch("app.api.dependencies.RedisCache"):
        cache = get_cache()
        assert cache is not None


def test_get_bgpq4_client():
    client = get_bgpq4_client()
    assert client is not None
    assert hasattr(client, "execute_with_retry")


def test_get_broker():
    broker = get_broker()
    assert broker is not None
