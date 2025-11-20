from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_bgpq4_client, get_broker, get_cache
from app.main import app


@pytest.mark.asyncio
async def test_route_set_expand():
    # Mock cache
    mock_cache = AsyncMock()
    mock_cache.get.return_value = None
    mock_cache.generate_key.return_value = "test-cache-key"

    # Mock bgpq4 client - parse_json_output is NOT async, so use MagicMock for it
    mock_client = AsyncMock()
    mock_client.execute_with_retry.return_value = '{"NN": []}'
    # parse_json_output is synchronous, not async
    mock_client.parse_json_output = MagicMock(return_value={"prefixes": [], "count": 0})

    # Override dependencies
    app.dependency_overrides[get_cache] = lambda: mock_cache
    app.dependency_overrides[get_bgpq4_client] = lambda: mock_client

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/route-set/expand?target=RS-EXAMPLE")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert "data" in data
    finally:
        # Clean up dependency overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_route_set_expand_cache_hit():
    """Test that cached data is returned when available."""
    cached_data = {"prefixes": ["192.0.2.0/24"], "count": 1}

    mock_cache = AsyncMock()
    mock_cache.get.return_value = cached_data
    mock_cache.generate_key.return_value = "test-cache-key"

    app.dependency_overrides[get_cache] = lambda: mock_cache

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/route-set/expand?target=RS-EXAMPLE")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["data"] == cached_data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_route_set_expand_non_json_format():
    """Test non-JSON format returns raw output."""
    mock_cache = AsyncMock()
    mock_cache.get.return_value = None
    mock_cache.generate_key.return_value = "test-cache-key"

    mock_client = AsyncMock()
    mock_client.execute_with_retry.return_value = "ip prefix-list test permit 192.0.2.0/24"
    mock_client.parse_json_output = MagicMock()

    app.dependency_overrides[get_cache] = lambda: mock_cache
    app.dependency_overrides[get_bgpq4_client] = lambda: mock_client

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/route-set/expand?target=RS-EXAMPLE&format=cisco")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert "output" in data["data"]
            # parse_json_output should NOT be called for non-json format
            mock_client.parse_json_output.assert_not_called()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_route_set_expand_async_timeout():
    """Test that timeout triggers async job dispatch."""
    mock_cache = AsyncMock()
    mock_cache.get.return_value = None
    mock_cache.generate_key.return_value = "test-cache-key"

    mock_client = AsyncMock()
    mock_client.execute_with_retry.side_effect = TimeoutError()

    mock_broker = AsyncMock()
    mock_task = AsyncMock()
    mock_task.task_id = "test-job-id"
    mock_broker.execute_bgpq4_query.kiq.return_value = mock_task

    app.dependency_overrides[get_cache] = lambda: mock_cache
    app.dependency_overrides[get_bgpq4_client] = lambda: mock_client
    app.dependency_overrides[get_broker] = lambda: mock_broker

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/route-set/expand?target=RS-EXAMPLE")
            assert response.status_code == 202
            data = response.json()
            assert data["status"] == "processing"
            assert data["job_id"] == "test-job-id"
    finally:
        app.dependency_overrides.clear()
