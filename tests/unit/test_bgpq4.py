from unittest.mock import AsyncMock, patch

import pytest

from app.bgpq4 import BGPq4Client
from app.exceptions import BGPq4ExecutionError, BGPq4ParseError, BGPq4TimeoutError


@pytest.fixture
def client():
    return BGPq4Client(binary_path="/usr/bin/bgpq4", default_sources=["RIPE", "RADB"])


def test_build_command_basic(client):
    cmd = client._build_command(target="AS-HURRICANE", sources=None, format="json")
    assert "/usr/bin/bgpq4" in cmd
    assert "-j" in cmd
    assert "-S" in cmd
    assert "RIPE,RADB" in cmd
    assert "AS-HURRICANE" in cmd


def test_build_command_with_aggregate(client):
    cmd = client._build_command(target="AS-HURRICANE", sources=None, format="json", aggregate=True)
    assert "-A" in cmd


def test_build_command_with_masklen(client):
    cmd = client._build_command(
        target="AS-HURRICANE",
        sources=None,
        format="json",
        min_masklen=24,
        max_masklen=32,
    )
    assert "-r" in cmd
    assert "24" in cmd
    assert "-R" in cmd
    assert "32" in cmd


def test_build_command_cisco_format(client):
    cmd = client._build_command(target="AS-HURRICANE", sources=None, format="cisco")
    assert "-j" not in cmd  # JSON flag should not be present


@pytest.mark.asyncio
async def test_execute_success(client):
    with patch("app.bgpq4.asyncio.create_subprocess_exec") as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b'{"prefixes": []}', b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        result = await client.execute(target="AS-HURRICANE", sources=None, format="json")
        assert result == '{"prefixes": []}'


@pytest.mark.asyncio
async def test_execute_failure(client):
    with patch("app.bgpq4.asyncio.create_subprocess_exec") as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"error message")
        mock_process.returncode = 1
        mock_exec.return_value = mock_process

        with pytest.raises(BGPq4ExecutionError) as exc_info:
            await client.execute(target="AS-HURRICANE", sources=None, format="json")
        assert exc_info.value.return_code == 1
        assert "error message" in exc_info.value.stderr


def test_parse_json_output_success(client):
    raw_output = '{"NN": [{"prefix": "192.0.2.0/24"}, {"prefix": "198.51.100.0/24"}]}'
    result = client.parse_json_output(raw_output)
    assert "prefixes" in result
    assert len(result["prefixes"]) == 2
    assert result["count"] == 2


def test_parse_json_output_empty(client):
    raw_output = '{"NN": []}'
    result = client.parse_json_output(raw_output)
    assert result["prefixes"] == []
    assert result["count"] == 0


def test_parse_json_output_invalid():
    client = BGPq4Client(binary_path="/usr/bin/bgpq4", default_sources=["RIPE"])
    with pytest.raises(BGPq4ParseError):
        client.parse_json_output("not valid json")


@pytest.mark.asyncio
async def test_execute_with_retry_success_after_failure():
    client = BGPq4Client(
        binary_path="/usr/bin/bgpq4",
        default_sources=["RIPE"],
        max_retries=3,
        retry_backoff=0.1,
    )

    with patch("app.bgpq4.asyncio.create_subprocess_exec") as mock_exec:
        # First call fails, second succeeds
        mock_process_fail = AsyncMock()
        mock_process_fail.communicate.return_value = (b"", b"connection error")
        mock_process_fail.returncode = 1

        mock_process_success = AsyncMock()
        mock_process_success.communicate.return_value = (b'{"NN": []}', b"")
        mock_process_success.returncode = 0

        mock_exec.side_effect = [mock_process_fail, mock_process_success]

        result = await client.execute_with_retry(target="AS-HURRICANE", sources=None, format="json")
        assert result == '{"NN": []}'
        assert mock_exec.call_count == 2


@pytest.mark.asyncio
async def test_execute_with_retry_max_retries_exceeded():
    client = BGPq4Client(
        binary_path="/usr/bin/bgpq4",
        default_sources=["RIPE"],
        max_retries=2,
        retry_backoff=0.1,
    )

    with patch("app.bgpq4.asyncio.create_subprocess_exec") as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"connection error")
        mock_process.returncode = 1
        mock_exec.return_value = mock_process

        with pytest.raises(BGPq4ExecutionError):
            await client.execute_with_retry(target="AS-HURRICANE", sources=None, format="json")
        # Initial attempt + 2 retries = 3 total calls
        assert mock_exec.call_count == 3


@pytest.mark.asyncio
async def test_execute_timeout(client):
    """Test that timeout raises BGPq4TimeoutError."""
    with patch("app.bgpq4.asyncio.create_subprocess_exec") as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.side_effect = TimeoutError()
        mock_exec.return_value = mock_process

        with pytest.raises(BGPq4TimeoutError) as exc_info:
            await client.execute(
                target="AS-HURRICANE", sources=None, format="json", timeout_seconds=1.0
            )
        assert exc_info.value.timeout_seconds == 1.0
        assert "timed out after 1.0s" in str(exc_info.value)


@pytest.mark.asyncio
async def test_execute_with_retry_timeout():
    """Test that timeout errors are retried."""
    client = BGPq4Client(
        binary_path="/usr/bin/bgpq4",
        default_sources=["RIPE"],
        max_retries=2,
        retry_backoff=0.1,
    )

    with patch("app.bgpq4.asyncio.create_subprocess_exec") as mock_exec:
        # First call times out, second succeeds
        mock_process_timeout = AsyncMock()
        mock_process_timeout.communicate.side_effect = TimeoutError()

        mock_process_success = AsyncMock()
        mock_process_success.communicate.return_value = (b'{"NN": []}', b"")
        mock_process_success.returncode = 0

        mock_exec.side_effect = [mock_process_timeout, mock_process_success]

        result = await client.execute_with_retry(target="AS-HURRICANE", sources=None, format="json")
        assert result == '{"NN": []}'
        assert mock_exec.call_count == 2
