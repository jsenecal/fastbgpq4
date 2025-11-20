from app.exceptions import (
    BGPq4Error,
    BGPq4ExecutionError,
    BGPq4ParseError,
    BGPq4TimeoutError,
    CacheError,
)


def test_bgpq4_error_base():
    error = BGPq4Error("test error")
    assert str(error) == "test error"


def test_bgpq4_execution_error():
    error = BGPq4ExecutionError("execution failed", return_code=1, stderr="error output")
    assert error.return_code == 1
    assert error.stderr == "error output"


def test_bgpq4_timeout_error():
    error = BGPq4TimeoutError("timeout after 5s", timeout_seconds=5.0)
    assert error.timeout_seconds == 5.0


def test_bgpq4_parse_error():
    error = BGPq4ParseError("failed to parse", output="bad output")
    assert error.output == "bad output"


def test_cache_error():
    error = CacheError("cache connection failed")
    assert str(error) == "cache connection failed"
