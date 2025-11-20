from typing import Any

from pydantic import BaseModel


class SyncResponse(BaseModel):
    """Response for completed synchronous queries."""

    status: str
    data: dict[str, Any]
    cache_ttl: int
    execution_time_ms: int


class AsyncResponse(BaseModel):
    """Response when query switches to async mode."""

    status: str
    job_id: str
    poll_url: str
    estimated_time_ms: int | None = None


class JobStatusResponse(BaseModel):
    """Response for job status polling."""

    status: str
    job_id: str
    data: dict[str, Any] | None = None
    error: str | None = None
    execution_time_ms: int | None = None
