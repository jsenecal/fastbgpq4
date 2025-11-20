from app.metrics import metrics


def test_metrics_initialized():
    assert metrics.request_count is not None
    assert metrics.request_duration is not None
    assert metrics.cache_hits is not None
    assert metrics.cache_misses is not None
    assert metrics.bgpq4_execution_duration is not None
    assert metrics.active_jobs is not None


def test_track_request():
    # Track the request which creates a labeled counter instance
    metrics.track_request("as_set", "expand", 200)

    # Get the labeled instance and verify it was incremented
    labeled = metrics.request_count.labels(resource="as_set", operation="expand", status_code=200)
    assert labeled._value.get() >= 1


def test_track_cache_hit():
    # Track cache hit
    metrics.track_cache_hit("as_set")

    # Get the labeled instance and verify it was incremented
    labeled = metrics.cache_hits.labels(resource="as_set")
    assert labeled._value.get() >= 1


def test_track_cache_miss():
    # Track cache miss
    metrics.track_cache_miss("as_set")

    # Get the labeled instance and verify it was incremented
    labeled = metrics.cache_misses.labels(resource="as_set")
    assert labeled._value.get() >= 1


def test_track_bgpq4_execution():
    """Test bgpq4 execution duration tracking."""
    metrics.track_bgpq4_execution(0.5)
    # Histogram doesn't expose easy access to count, just verify no exception


def test_increment_decrement_active_jobs():
    """Test active jobs gauge increment and decrement."""
    initial = metrics.active_jobs._value.get()
    metrics.increment_active_jobs()
    assert metrics.active_jobs._value.get() == initial + 1
    metrics.decrement_active_jobs()
    assert metrics.active_jobs._value.get() == initial
