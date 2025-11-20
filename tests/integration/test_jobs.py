from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_cache
from app.main import app


@pytest.mark.asyncio
async def test_get_job_status_completed():
    # Mock cache
    mock_cache = AsyncMock()
    mock_cache.get.return_value = {
        "status": "completed",
        "job_id": "test-job",
        "data": {"prefixes": [], "count": 0},
        "execution_time_ms": 1500,
    }

    # Override dependencies
    app.dependency_overrides[get_cache] = lambda: mock_cache

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/jobs/test-job")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert "data" in data
    finally:
        # Clean up dependency overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_job_status_processing():
    # Mock cache
    mock_cache = AsyncMock()
    mock_cache.get.return_value = {
        "status": "processing",
        "job_id": "test-job",
    }

    # Override dependencies
    app.dependency_overrides[get_cache] = lambda: mock_cache

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/jobs/test-job")
            assert response.status_code == 202
            data = response.json()
            assert data["status"] == "processing"
    finally:
        # Clean up dependency overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_job_status_not_found():
    # Mock cache
    mock_cache = AsyncMock()
    mock_cache.get.return_value = None

    # Override dependencies
    app.dependency_overrides[get_cache] = lambda: mock_cache

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/jobs/nonexistent")
            assert response.status_code == 404
    finally:
        # Clean up dependency overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_job_status_failed():
    """Test that failed job status returns 200 with error info."""
    mock_cache = AsyncMock()
    mock_cache.get.return_value = {
        "status": "failed",
        "job_id": "test-job",
        "error": "BGPq4 execution failed",
        "execution_time_ms": 500,
    }

    app.dependency_overrides[get_cache] = lambda: mock_cache

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/jobs/test-job")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "failed"
            assert "error" in data
    finally:
        app.dependency_overrides.clear()
