from prometheus_client import Counter, Gauge, Histogram


class Metrics:
    """Prometheus metrics for the application."""

    def __init__(self):
        self.request_count = Counter(
            "fastbgpq4_requests_total",
            "Total number of requests",
            ["resource", "operation", "status_code"],
        )

        self.request_duration = Histogram(
            "fastbgpq4_request_duration_seconds",
            "Request duration in seconds",
            ["resource", "operation"],
        )

        self.cache_hits = Counter("fastbgpq4_cache_hits_total", "Total cache hits", ["resource"])

        self.cache_misses = Counter(
            "fastbgpq4_cache_misses_total", "Total cache misses", ["resource"]
        )

        self.bgpq4_execution_duration = Histogram(
            "fastbgpq4_bgpq4_execution_duration_seconds",
            "BGPq4 execution duration in seconds",
        )

        self.active_jobs = Gauge("fastbgpq4_active_jobs", "Number of active background jobs")

    def track_request(self, resource: str, operation: str, status_code: int):
        """Track a request."""
        self.request_count.labels(
            resource=resource, operation=operation, status_code=status_code
        ).inc()

    def track_cache_hit(self, resource: str):
        """Track a cache hit."""
        self.cache_hits.labels(resource=resource).inc()

    def track_cache_miss(self, resource: str):
        """Track a cache miss."""
        self.cache_misses.labels(resource=resource).inc()

    def track_bgpq4_execution(self, duration_seconds: float):
        """Track bgpq4 execution duration."""
        self.bgpq4_execution_duration.observe(duration_seconds)

    def increment_active_jobs(self):
        """Increment active job count."""
        self.active_jobs.inc()

    def decrement_active_jobs(self):
        """Decrement active job count."""
        self.active_jobs.dec()


# Global metrics instance
metrics = Metrics()
