from pydantic import BaseModel, field_validator


class BGPQueryRequest(BaseModel):
    """Request model for BGP queries."""

    target: str
    sources: list[str] | None = None
    format: str = "json"
    cache_ttl: int | None = None
    skip_cache: bool = False
    aggregate: bool = False
    min_masklen: int | None = None
    max_masklen: int | None = None

    @field_validator("min_masklen", "max_masklen")
    @classmethod
    def validate_masklen(cls, v):
        if v is not None and (v < 0 or v > 128):
            raise ValueError("Masklen must be between 0 and 128")
        return v
