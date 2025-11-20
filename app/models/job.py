from enum import Enum


class JobStatus(str, Enum):
    """Job execution status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
