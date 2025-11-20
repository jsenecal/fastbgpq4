import json
import logging

from app.logging import JSONFormatter, setup_logging


def test_json_formatter():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert data["message"] == "test message"
    assert data["level"] == "INFO"
    assert "timestamp" in data


def test_setup_logging():
    logger = setup_logging()
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0


def test_json_formatter_with_exception():
    """Test that exception info is included in formatted output."""
    formatter = JSONFormatter()
    try:
        raise ValueError("test error")
    except ValueError:
        import sys

        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg="error occurred",
        args=(),
        exc_info=exc_info,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert "exception" in data
    assert "ValueError: test error" in data["exception"]


def test_json_formatter_with_extra_fields():
    """Test that extra fields are included in formatted output."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )
    # Add extra field
    record.request_id = "abc123"
    record.target = "AS-HURRICANE"

    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert data["request_id"] == "abc123"
    assert data["target"] == "AS-HURRICANE"


def test_setup_logging_debug_level():
    """Test that custom log level can be set."""
    logger = setup_logging(level="DEBUG")
    assert logger.level == logging.DEBUG
