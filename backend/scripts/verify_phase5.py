#!/usr/bin/env python3
"""Verify Phase 5: Redis caching layer and match cache integration."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.schemas.match import JobMatch  # noqa: E402
from app.services.cache import (  # noqa: E402
    hash_text,
    match_results_key,
    resume_embedding_key,
)
from app.services.match_cache import get_cached_matches, set_cached_matches  # noqa: E402
from app.services.matcher import stream_job_match  # noqa: E402
from app.services.resume_ingest import ParsedResume  # noqa: E402
from app.schemas.resume import ResumeSignals  # noqa: E402

SAMPLE_RESUME = BACKEND_ROOT / "data" / "sample_resume_aarav_mehta.txt"


def verify_cache_keys() -> None:
    text = "Senior Python engineer with FastAPI experience."
    assert hash_text(text) == hash_text("  Senior   Python engineer\nwith FastAPI experience. ")
    assert match_results_key(text).startswith("arya:v1:match:")
    assert resume_embedding_key(text).startswith("arya:v1:resume_emb:")
    print("OK  cache key helpers normalize and version keys")


async def verify_match_cache_roundtrip() -> None:
    resume = SAMPLE_RESUME.read_text(encoding="utf-8")
    matches = [
        JobMatch(
            job_id="job_005",
            title="Python Backend Developer",
            company="Mentoria",
            location="Mumbai, India",
            remote="hybrid",
            match_score=94,
            reasoning="Strong fit based on your FastAPI and LangGraph production experience.",
            highlight_bullet="Architected and shipped the core outreach agent",
        )
    ]

    stored: dict[str, str] = {}

    async def mock_setex(key, ttl, value):
        stored[key] = value
        return True

    async def mock_get(key):
        return stored.get(key)

    mock_client = AsyncMock()
    mock_client.setex = mock_setex
    mock_client.get = mock_get

    with patch("app.services.cache.get_redis", return_value=mock_client):
        assert await set_cached_matches(resume, matches) is True
        cached = await get_cached_matches(resume)
        assert cached is not None
        assert cached[0].job_id == "job_005"

    print("OK  match results cache roundtrip")


async def verify_matcher_cache_hit_stream() -> None:
    resume = SAMPLE_RESUME.read_text(encoding="utf-8")
    cached_matches = [
        JobMatch(
            job_id=f"job_00{i}",
            title=f"Role {i}",
            company=f"Co {i}",
            location="Bengaluru, India",
            remote="hybrid",
            match_score=95 - i,
            reasoning="Personalized reasoning one. Personalized reasoning two.",
            highlight_bullet="Architected and shipped the core outreach agent",
        )
        for i in range(1, 6)
    ]

    parsed = ParsedResume(
        raw_text=resume,
        signals=ResumeSignals(years_experience=5, location="Bengaluru, India", skills=["Python"]),
        embedding=None,
    )

    session = AsyncMock()
    chunks: list[str] = []

    with (
        patch("app.services.matcher.ingest_resume", AsyncMock(return_value=parsed)),
        patch("app.services.matcher.get_cached_matches", AsyncMock(return_value=cached_matches)),
        patch("app.services.matcher.embed_text", AsyncMock()) as mock_embed,
        patch("app.services.matcher.rank_jobs_with_llm", AsyncMock()) as mock_rank,
    ):
        async for chunk in stream_job_match(session, resume_text=resume):
            chunks.append(chunk)

    body = "".join(chunks)
    assert '"cache_hit": true' in body
    assert body.count("event: match") == 5
    mock_embed.assert_not_called()
    mock_rank.assert_not_called()
    print("OK  matcher uses cache hit path (skips embed + LLM)")


def verify_health_reports_redis() -> None:
    from fastapi.testclient import TestClient  # noqa: E402

    from app.main import app  # noqa: E402

    client = TestClient(app)
    with (
        patch("app.api.health.ping_redis", AsyncMock(return_value={"status": "connected", "pong": True})),
        patch("app.api.health.redis_available", return_value=True),
        patch("app.api.health.sentry_enabled", return_value=False),
    ):
        response = client.get("/api/health")
    body = response.json()
    assert body["redis"] == "connected"
    assert body["cache_enabled"] is True
    print("OK  /api/health reports redis status")


def main() -> None:
    verify_cache_keys()
    asyncio.run(verify_match_cache_roundtrip())
    asyncio.run(verify_matcher_cache_hit_stream())
    verify_health_reports_redis()
    print("Phase 5 verification passed.")


if __name__ == "__main__":
    main()
