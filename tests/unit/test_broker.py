from taskiq import InMemoryBroker

from app.tasks.broker import get_broker


def test_get_broker():
    broker = get_broker("redis://localhost:6379/0")
    assert broker is not None
    assert hasattr(broker, "startup")
    assert hasattr(broker, "shutdown")


def test_get_broker_in_memory():
    """Test that non-redis URL returns InMemoryBroker."""
    broker = get_broker("memory://")
    assert isinstance(broker, InMemoryBroker)
