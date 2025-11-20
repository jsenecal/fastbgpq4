from unittest.mock import AsyncMock, patch

import pytest

from app.models.job import JobStatus
from app.tasks.bgpq4_tasks import execute_bgpq4_query


@pytest.mark.asyncio
async def test_execute_bgpq4_query_success():
    with patch("app.tasks.bgpq4_tasks.BGPq4Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.execute_with_retry.return_value = '{"NN": []}'
        mock_client.parse_json_output.return_value = {"prefixes": [], "count": 0}
        mock_client_class.return_value = mock_client

        with patch("app.tasks.bgpq4_tasks.RedisCache") as mock_cache_class:
            mock_cache = AsyncMock()
            mock_cache_class.return_value = mock_cache

            result = await execute_bgpq4_query(
                job_id="test-job",
                target="AS-HURRICANE",
                sources=None,
                format="json",
                aggregate=False,
                min_masklen=None,
                max_masklen=None,
                cache_ttl=300,
            )

            assert result["status"] == JobStatus.COMPLETED
            assert "data" in result


@pytest.mark.asyncio
async def test_execute_bgpq4_query_failure():
    with patch("app.tasks.bgpq4_tasks.BGPq4Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.execute_with_retry.side_effect = Exception("Connection failed")
        mock_client_class.return_value = mock_client

        with patch("app.tasks.bgpq4_tasks.RedisCache") as mock_cache_class:
            mock_cache = AsyncMock()
            mock_cache_class.return_value = mock_cache

            result = await execute_bgpq4_query(
                job_id="test-job",
                target="AS-HURRICANE",
                sources=None,
                format="json",
                aggregate=False,
                min_masklen=None,
                max_masklen=None,
                cache_ttl=300,
            )

            assert result["status"] == JobStatus.FAILED
            assert "error" in result


@pytest.mark.asyncio
async def test_execute_bgpq4_query_non_json_format():
    """Test non-JSON format returns raw output."""
    with patch("app.tasks.bgpq4_tasks.BGPq4Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.execute_with_retry.return_value = "ip prefix-list test permit 192.0.2.0/24"
        mock_client_class.return_value = mock_client

        with patch("app.tasks.bgpq4_tasks.RedisCache") as mock_cache_class:
            mock_cache = AsyncMock()
            mock_cache_class.return_value = mock_cache

            result = await execute_bgpq4_query(
                job_id="test-job",
                target="AS-HURRICANE",
                sources=None,
                format="cisco",  # Non-JSON format
                aggregate=False,
                min_masklen=None,
                max_masklen=None,
                cache_ttl=300,
            )

            assert result["status"] == JobStatus.COMPLETED
            assert "output" in result["data"]
            # parse_json_output should NOT be called for non-json format
            mock_client.parse_json_output.assert_not_called()


@pytest.mark.asyncio
async def test_execute_bgpq4_query_bgpq4_error():
    """Test BGPq4Error handling."""
    from app.exceptions import BGPq4ExecutionError

    with patch("app.tasks.bgpq4_tasks.BGPq4Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.execute_with_retry.side_effect = BGPq4ExecutionError(
            message="bgpq4 failed", return_code=1, stderr="error"
        )
        mock_client_class.return_value = mock_client

        with patch("app.tasks.bgpq4_tasks.RedisCache") as mock_cache_class:
            mock_cache = AsyncMock()
            mock_cache_class.return_value = mock_cache

            result = await execute_bgpq4_query(
                job_id="test-job",
                target="AS-HURRICANE",
                sources=None,
                format="json",
                aggregate=False,
                min_masklen=None,
                max_masklen=None,
                cache_ttl=300,
            )

            assert result["status"] == JobStatus.FAILED
            assert "error" in result
            assert "bgpq4 failed" in result["error"]
