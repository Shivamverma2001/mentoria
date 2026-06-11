from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    redis: str
    cache_enabled: bool
    sentry: Literal["enabled", "disabled"]
    database: str | None = None
    jobs_count: int | None = None
    error: str | None = Field(default=None, description="Present when database is disconnected")
