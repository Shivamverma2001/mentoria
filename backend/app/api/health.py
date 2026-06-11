from typing import Literal

from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import async_session_factory
from app.core.redis import ping_redis, redis_available
from app.core.sentry import sentry_enabled
from app.schemas.health import HealthResponse
from app.services.seed import count_jobs

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    redis_status = await ping_redis()
    status: Literal["ok", "degraded"] = "ok"
    database: str | None = None
    jobs_count: int | None = None
    error: str | None = None

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            jobs_count = await count_jobs(session)
        database = "connected"
    except Exception as exc:
        status = "degraded"
        database = "disconnected"
        error = str(exc)

    if database != "connected" or redis_status["status"] != "connected":
        status = "degraded"

    return HealthResponse(
        status=status,
        redis=redis_status["status"],
        cache_enabled=redis_available(),
        sentry="enabled" if sentry_enabled() else "disabled",
        database=database,
        jobs_count=jobs_count,
        error=error,
    )
