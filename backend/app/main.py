import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.jobs import router as jobs_router
from app.core.config import settings
from app.core.database import async_session_factory, engine
from app.core.db_init import init_database
from app.services.seed import count_jobs

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.job_count = 0
    try:
        async with async_session_factory() as session:
            app.state.job_count = await init_database(session)
        logger.info("Database initialized with %s jobs", app.state.job_count)
    except Exception as exc:
        logger.warning("Database init skipped (is Postgres running?): %s", exc)
    yield
    await engine.dispose()


app = FastAPI(
    title="Arya Smart Job Matcher",
    description="Mentoria take-home: resume-to-job matching with streaming results",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)


@app.get("/api/health")
async def health() -> dict:
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            job_count = await count_jobs(session)
        return {
            "status": "ok",
            "database": "connected",
            "jobs_count": job_count,
        }
    except Exception as exc:
        return {
            "status": "degraded",
            "database": "disconnected",
            "error": str(exc),
        }
