from taskiq import InMemoryBroker
from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend


def get_broker(redis_url: str) -> ListQueueBroker | InMemoryBroker:
    """Get Taskiq broker instance."""
    if redis_url.startswith("redis://"):
        # Production: Redis broker
        result_backend = RedisAsyncResultBackend(redis_url)
        broker = ListQueueBroker(redis_url).with_result_backend(result_backend)
        return broker
    else:
        # Testing: In-memory broker
        return InMemoryBroker()
