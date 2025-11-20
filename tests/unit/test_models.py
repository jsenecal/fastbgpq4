import pytest
from pydantic import ValidationError

from app.models.job import JobStatus
from app.models.requests import BGPQueryRequest
from app.models.responses import AsyncResponse, SyncResponse


def test_bgp_query_request_defaults():
    req = BGPQueryRequest(target="AS-HURRICANE")
    assert req.target == "AS-HURRICANE"
    assert req.sources is None
    assert req.format == "json"
    assert req.skip_cache is False
    assert req.aggregate is False
    assert req.cache_ttl is None


def test_bgp_query_request_with_masklen():
    req = BGPQueryRequest(target="AS-HURRICANE", min_masklen=24, max_masklen=32)
    assert req.min_masklen == 24
    assert req.max_masklen == 32


def test_bgp_query_request_invalid_masklen():
    with pytest.raises(ValidationError):
        BGPQueryRequest(target="AS-HURRICANE", min_masklen=129)


def test_sync_response_structure():
    resp = SyncResponse(
        status="completed",
        data={"prefixes": ["192.0.2.0/24"], "count": 1},
        cache_ttl=300,
        execution_time_ms=450,
    )
    assert resp.status == "completed"
    assert resp.data["count"] == 1


def test_async_response_structure():
    resp = AsyncResponse(
        status="processing",
        job_id="test-job-id",
        poll_url="/api/v1/jobs/test-job-id",
    )
    assert resp.status == "processing"
    assert resp.job_id == "test-job-id"


def test_job_status_enum():
    assert JobStatus.PENDING == "pending"
    assert JobStatus.PROCESSING == "processing"
    assert JobStatus.COMPLETED == "completed"
    assert JobStatus.FAILED == "failed"
