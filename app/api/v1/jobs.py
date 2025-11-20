from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_cache
from app.cache import RedisCache
from app.models.job import JobStatus
from app.models.responses import JobStatusResponse

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("/{job_id}")
async def get_job_status(
    job_id: str,
    cache: RedisCache = Depends(get_cache),
):
    """Get status of background job."""
    # Job results are stored in cache with job ID as key
    job_key = f"job:{job_id}"
    job_data = await cache.get(job_key)

    if job_data is None:
        raise HTTPException(status_code=404, detail="Job not found")

    status = job_data.get("status")

    if status == JobStatus.COMPLETED:
        return JobStatusResponse(
            status=status,
            job_id=job_id,
            data=job_data.get("data"),
            execution_time_ms=job_data.get("execution_time_ms"),
        )
    elif status == JobStatus.FAILED:
        return JobStatusResponse(
            status=status,
            job_id=job_id,
            error=job_data.get("error"),
            execution_time_ms=job_data.get("execution_time_ms"),
        )
    else:
        # Still processing
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=202,
            content={
                "status": status,
                "job_id": job_id,
            },
        )
