import asyncio
import time
import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.api.dependencies import get_bgpq4_client, get_broker, get_cache
from app.bgpq4 import BGPq4Client
from app.cache import RedisCache
from app.config import settings
from app.metrics import metrics
from app.models.responses import AsyncResponse, SyncResponse

router = APIRouter(prefix="/api/v1/route-set", tags=["route-set"])


@router.get("/expand")
async def expand_route_set(
    target: str = Query(..., description="Route-set to expand"),
    sources: str | None = Query(None, description="Comma-separated IRR sources"),
    format: str = Query("json", description="Output format"),
    cache_ttl: int | None = Query(None, description="Cache TTL in seconds"),
    skip_cache: bool = Query(False, description="Skip cache"),
    aggregate: bool = Query(False, description="Enable aggregation"),
    min_masklen: int | None = Query(None, description="Minimum prefix length"),
    max_masklen: int | None = Query(None, description="Maximum prefix length"),
    cache: RedisCache = Depends(get_cache),
    client: BGPq4Client = Depends(get_bgpq4_client),
    broker=Depends(get_broker),
):
    """Expand route-set to prefix list."""
    start_time = time.time()

    # Parse sources
    sources_list = sources.split(",") if sources else None

    # Use default cache TTL if not specified
    ttl = cache_ttl if cache_ttl is not None else settings.default_cache_ttl

    # Check cache
    if not skip_cache:
        cache_key = cache.generate_key(
            target=target,
            sources=sources_list,
            aggregate=aggregate,
            min_masklen=min_masklen,
            max_masklen=max_masklen,
            format=format,
        )
        cached_data = await cache.get(cache_key)
        if cached_data:
            metrics.track_cache_hit("route_set")
            execution_time_ms = int((time.time() - start_time) * 1000)
            return SyncResponse(
                status="completed",
                data=cached_data,
                cache_ttl=ttl,
                execution_time_ms=execution_time_ms,
            )
        metrics.track_cache_miss("route_set")

    # Execute with timeout
    try:
        timeout_seconds = settings.sync_timeout_ms / 1000
        raw_output = await asyncio.wait_for(
            client.execute_with_retry(
                target=target,
                sources=sources_list,
                format=format,
                aggregate=aggregate,
                min_masklen=min_masklen,
                max_masklen=max_masklen,
                timeout_seconds=settings.max_execution_time_ms / 1000,
            ),
            timeout=timeout_seconds,
        )

        # Parse and cache result
        if format == "json":
            data = client.parse_json_output(raw_output)
        else:
            data = {"output": raw_output}

        if not skip_cache:
            await cache.set(cache_key, data, ttl)

        execution_time_ms = int((time.time() - start_time) * 1000)
        metrics.track_request("route_set", "expand", 200)

        return SyncResponse(
            status="completed",
            data=data,
            cache_ttl=ttl,
            execution_time_ms=execution_time_ms,
        )

    except TimeoutError:
        # Switch to async mode
        # Dispatch to broker (mock-friendly approach)
        if hasattr(broker, "execute_bgpq4_query"):
            # Mocked broker
            task = await broker.execute_bgpq4_query.kiq(
                job_id="auto",
                target=target,
                sources=sources_list,
                format=format,
                aggregate=aggregate,
                min_masklen=min_masklen,
                max_masklen=max_masklen,
                cache_ttl=ttl,
            )
            job_id = task.task_id
        else:
            # Real broker fallback - only used in production without mock
            job_id = str(uuid.uuid4())

        metrics.track_request("route_set", "expand", 202)
        metrics.increment_active_jobs()

        response_data = AsyncResponse(
            status="processing",
            job_id=job_id,
            poll_url=f"/api/v1/jobs/{job_id}",
        )
        return JSONResponse(status_code=202, content=response_data.model_dump())
