class BGPq4Error(Exception):
    """Base exception for BGPq4 errors."""

    pass


class BGPq4ExecutionError(BGPq4Error):
    """BGPq4 process execution failed."""

    def __init__(self, message: str, return_code: int, stderr: str):
        super().__init__(message)
        self.return_code = return_code
        self.stderr = stderr


class BGPq4TimeoutError(BGPq4Error):
    """BGPq4 process timed out."""

    def __init__(self, message: str, timeout_seconds: float):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


class BGPq4ParseError(BGPq4Error):
    """Failed to parse BGPq4 output."""

    def __init__(self, message: str, output: str):
        super().__init__(message)
        self.output = output


class CacheError(Exception):
    """Cache operation failed."""

    pass
