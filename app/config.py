from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration."""

    # BGPq4
    bgpq4_binary: str = "/usr/bin/bgpq4"
    irr_sources: list[str] | str = ["RIPE", "RADB", "ARIN"]

    # Timing
    sync_timeout_ms: int = 1000
    max_execution_time_ms: int = 30000

    # Retry
    max_retries: int = 3
    retry_backoff_factor: float = 2.0

    # Cache
    default_cache_ttl: int = 300
    max_cache_ttl: int = 3600

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    job_result_ttl: int = 3600

    # API
    api_title: str = "FastBGPQ4"
    api_version: str = "v1"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("irr_sources", mode="before")
    @classmethod
    def parse_irr_sources(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",")]
        return v


# Global settings instance
settings = Settings()
