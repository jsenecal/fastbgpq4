import logging
import time
from typing import Any

from app.bgpq4 import BGPq4Client
from app.cache import RedisCache
from app.config import settings
from app.exceptions import BGPq4Error
from app.models.job import JobStatus

logger = logging.getLogger("fastbgpq4")


async def execute_bgpq4_query(
    job_id: str,
    target: str,
    sources: list[str] | None,
    format: str,
    aggregate: bool,
    min_masklen: int | None,
    max_masklen: int | None,
    cache_ttl: int,
) -> dict[str, Any]:
    """Execute bgpq4 query as background task."""
    start_time = time.time()

    try:
        # Initialize clients
        client = BGPq4Client(
            binary_path=settings.bgpq4_binary,
            default_sources=settings.irr_sources,
            max_retries=settings.max_retries,
            retry_backoff=settings.retry_backoff_factor,
        )

        cache = RedisCache(settings.redis_url)

        # Execute query
        raw_output = await client.execute_with_retry(
            target=target,
            sources=sources,
            format=format,
            aggregate=aggregate,
            min_masklen=min_masklen,
            max_masklen=max_masklen,
            timeout_seconds=settings.max_execution_time_ms / 1000,
        )

        # Parse output
        if format == "json":
            data = client.parse_json_output(raw_output)
        else:
            data = {"output": raw_output}

        # Cache result
        cache_key = cache.generate_key(
            target=target,
            sources=sources,
            aggregate=aggregate,
            min_masklen=min_masklen,
            max_masklen=max_masklen,
            format=format,
        )
        await cache.set(cache_key, data, cache_ttl)
        await cache.close()

        execution_time_ms = int((time.time() - start_time) * 1000)

        return {
            "status": JobStatus.COMPLETED,
            "job_id": job_id,
            "data": data,
            "execution_time_ms": execution_time_ms,
        }

    except BGPq4Error as e:
        logger.error(f"BGPq4 error in job {job_id}: {e}")
        execution_time_ms = int((time.time() - start_time) * 1000)
        return {
            "status": JobStatus.FAILED,
            "job_id": job_id,
            "error": str(e),
            "execution_time_ms": execution_time_ms,
        }

    except Exception as e:
        logger.exception(f"Unexpected error in job {job_id}: {e}")
        execution_time_ms = int((time.time() - start_time) * 1000)
        return {
            "status": JobStatus.FAILED,
            "job_id": job_id,
            "error": f"Internal error: {str(e)}",
            "execution_time_ms": execution_time_ms,
        }
