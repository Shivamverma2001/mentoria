import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.match import router as match_router
from app.api.resume import router as resume_router
from app.api.root import router as root_router
from app.core.config import settings
from app.core.database import async_session_factory, engine
from app.core.db_init import init_database
from app.core.redis import close_redis, init_redis
from app.core.sentry import init_sentry
from app.schemas.errors import ErrorResponse
from app.services.llm_ranker import MatchRankingError
from app.services.resume_errors import ResumeEmbeddingError, ResumeParseError
logger = logging.getLogger(__name__)

init_sentry()


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
    description=(
        "Mentoria take-home API: ingest resumes, match against job descriptions via "
        "pgvector + LLM, stream top 5 results over SSE. See `/docs` for schemas."
    ),
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "meta", "description": "API discovery"},
        {"name": "health", "description": "Liveness and dependency checks"},
        {"name": "jobs", "description": "Job catalog (seeded from jobs.json)"},
        {"name": "resume", "description": "Resume parsing and embedding"},
        {"name": "match", "description": "Smart job matching (SSE stream)"},
    ],
)


@app.exception_handler(ResumeParseError)
async def resume_parse_error_handler(_request: Request, exc: ResumeParseError) -> JSONResponse:
    body = ErrorResponse(detail=exc.message, code=exc.code)
    return JSONResponse(status_code=400, content=body.model_dump())


@app.exception_handler(ResumeEmbeddingError)
async def resume_embedding_error_handler(_request: Request, exc: ResumeEmbeddingError) -> JSONResponse:
    body = ErrorResponse(detail=exc.message, code=exc.code)
    return JSONResponse(status_code=502, content=body.model_dump())


@app.exception_handler(MatchRankingError)
async def match_ranking_error_handler(_request: Request, exc: MatchRankingError) -> JSONResponse:
    body = ErrorResponse(detail=exc.message, code=exc.code)
    return JSONResponse(status_code=502, content=body.model_dump())


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(root_router)
app.include_router(health_router)
app.include_router(jobs_router)
app.include_router(resume_router)
app.include_router(match_router)
