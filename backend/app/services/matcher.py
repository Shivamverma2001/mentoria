import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.match import DoneEvent, ErrorEvent, JobMatch, StatusEvent
from app.services.embeddings import embed_text
from app.services.job_embeddings import ensure_job_embeddings
from app.services.llm_ranker import MatchRankingError, rank_jobs_with_llm
from app.services.match_cache import get_cached_matches, set_cached_matches
from app.services.resume_ingest import ParsedResume, ingest_resume
from app.services.vector_search import search_similar_jobs

logger = logging.getLogger(__name__)

_PROGRESS_STAGES: tuple[StatusEvent, ...] = (
    StatusEvent(stage="embedding"),
    StatusEvent(stage="retrieving"),
    StatusEvent(stage="ranking"),
)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _emit_cached_stream(
    matches: list[JobMatch],
    started: float,
) -> AsyncIterator[str]:
    for stage in _PROGRESS_STAGES:
        yield _sse("status", stage.model_dump())
        await asyncio.sleep(0.02)

    for match in matches:
        yield _sse("match", match.model_dump())
        await asyncio.sleep(0.05)

    duration_ms = int((time.perf_counter() - started) * 1000)
    yield _sse(
        "done",
        DoneEvent(total=len(matches), duration_ms=duration_ms, cache_hit=True).model_dump(),
    )
    logger.info("Match cache stream complete: %s results, %sms", len(matches), duration_ms)


async def stream_job_match(
    session: AsyncSession,
    *,
    resume_text: str | None = None,
    resume_file: UploadFile | None = None,
) -> AsyncIterator[str]:
    started = time.perf_counter()

    try:
        yield _sse("status", StatusEvent(stage="parsing").model_dump())

        parsed: ParsedResume = await ingest_resume(
            resume_text=resume_text,
            resume_file=resume_file,
            embed=False,
        )

        cached_matches = await get_cached_matches(parsed.raw_text)
        if cached_matches:
            async for chunk in _emit_cached_stream(cached_matches, started):
                yield chunk
            return

        parsed.embedding = await embed_text(parsed.raw_text)

        yield _sse("status", StatusEvent(stage="embedding").model_dump())
        embedded = await ensure_job_embeddings(session)

        yield _sse("status", StatusEvent(stage="retrieving").model_dump())
        if parsed.embedding is None:
            raise MatchRankingError("Resume embedding missing after ingest.", "missing_embedding")

        shortlist = await search_similar_jobs(session, parsed.embedding)
        if not shortlist:
            raise MatchRankingError("No jobs with embeddings available for matching.", "no_jobs")

        yield _sse("status", StatusEvent(stage="ranking").model_dump())
        matches: list[JobMatch] = await rank_jobs_with_llm(parsed, shortlist)
        await set_cached_matches(parsed.raw_text, matches)

        for match in matches:
            yield _sse("match", match.model_dump())
            await asyncio.sleep(0.05)

        duration_ms = int((time.perf_counter() - started) * 1000)
        yield _sse(
            "done",
            DoneEvent(total=len(matches), duration_ms=duration_ms, cache_hit=False).model_dump(),
        )
        logger.info(
            "Match stream complete: %s results, %s jobs embedded this run, %sms",
            len(matches),
            embedded,
            duration_ms,
        )

    except Exception as exc:
        logger.exception("Match stream failed")
        code = getattr(exc, "code", "match_failed")
        message = getattr(exc, "message", str(exc))
        yield _sse("error", ErrorEvent(message=f"{message} (code={code})").model_dump())
