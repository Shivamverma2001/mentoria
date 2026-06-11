import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.jobs import router as jobs_router
from app.api.match import router as match_router
from app.api.resume import router as resume_router
from app.core.config import settings
from app.core.database import async_session_factory, engine
from app.core.db_init import init_database
from app.core.redis import close_redis, init_redis, ping_redis, redis_available
from app.services.llm_ranker import MatchRankingError
from app.services.resume_errors import ResumeEmbeddingError, ResumeParseError
from app.services.seed import count_jobs

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.job_count = 0
    app.state.redis_connected = await init_redis()

    try:
        async with async_session_factory() as session:
            app.state.job_count = await init_database(session)
        logger.info("Database initialized with %s jobs", app.state.job_count)
    except Exception as exc:
        logger.warning("Database init skipped (is Postgres running?): %s", exc)

    yield

    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="Arya Smart Job Matcher",
    description="Mentoria take-home: resume-to-job matching with streaming results",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(ResumeParseError)
async def resume_parse_error_handler(_request: Request, exc: ResumeParseError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(ResumeEmbeddingError)
async def resume_embedding_error_handler(_request: Request, exc: ResumeEmbeddingError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(MatchRankingError)
async def match_ranking_error_handler(_request: Request, exc: MatchRankingError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"detail": exc.message, "code": exc.code},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(resume_router)
app.include_router(match_router)


@app.get("/api/health")
async def health() -> dict:
    redis_status = await ping_redis()
    payload: dict = {
        "status": "ok",
        "redis": redis_status["status"],
        "cache_enabled": redis_available(),
    }

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            job_count = await count_jobs(session)
        payload["database"] = "connected"
        payload["jobs_count"] = job_count
    except Exception as exc:
        payload["status"] = "degraded"
        payload["database"] = "disconnected"
        payload["error"] = str(exc)

    if payload.get("database") != "connected" or redis_status["status"] != "connected":
        payload["status"] = "degraded"

    return payload
