#!/usr/bin/env python3
"""Verify Phase 4: matching pipeline, validation, and SSE stream."""

import asyncio
import sys
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.schemas.match import JobMatch  # noqa: E402
from app.schemas.ranking import RankingItem, RankingResponse  # noqa: E402
from app.services.llm_ranker import _build_matches  # noqa: E402
from app.services.match_validation import (  # noqa: E402
    finalize_match,
    highlight_in_resume,
    reasoning_is_valid,
)
from app.services.matcher import stream_job_match  # noqa: E402
from app.services.resume_ingest import ParsedResume  # noqa: E402
from app.schemas.resume import ResumeSignals  # noqa: E402
from app.models.job import Job  # noqa: E402

SAMPLE_RESUME = BACKEND_ROOT / "data" / "sample_resume_aarav_mehta.txt"


def _sample_job(job_id: str, title: str, company: str) -> Job:
    return Job(
        id=job_id,
        title=title,
        company=company,
        location="Bengaluru, India",
        remote="hybrid",
        experience_min_years=3,
        experience_max_years=7,
        salary_range_inr_lpa="25-40",
        salary_range_usd=None,
        posted_date=date(2026, 4, 15),
        skills_required=["Python", "FastAPI"],
        description="Build AI-powered backend systems.",
        apply_url="https://example.com",
        embedding=None,
    )


def verify_validation() -> None:
    resume = SAMPLE_RESUME.read_text(encoding="utf-8")
    bullet = "Architected and shipped the core outreach agent"
    assert highlight_in_resume(bullet, resume)
    assert reasoning_is_valid(
        "Your LangGraph agent experience maps directly to this role. "
        "The team's FastAPI stack matches your recent migration work."
    )
    print("OK  match validation helpers")


def verify_build_matches() -> None:
    resume = SAMPLE_RESUME.read_text(encoding="utf-8")
    jobs = [
        _sample_job("job_005", "Python Backend Developer", "Mentoria"),
        _sample_job("job_025", "Backend Engineer - Agentic", "Glean"),
        _sample_job("job_002", "AI Engineer", "Sarvam AI"),
        _sample_job("job_019", "AI Full Stack Developer", "Rocketlane"),
        _sample_job("job_015", "Founding Engineer", "stealth"),
        _sample_job("job_003", "Full Stack Developer", "Zepto"),
    ]
    response = RankingResponse(
        matches=[
            RankingItem(
                job_id="job_005",
                match_score=94,
                reasoning=(
                    "Your production LangGraph and FastAPI work at Kindred Labs is a strong fit for Mentoria's Arya backend. "
                    "You have already shipped agentic job-matching patterns similar to this role."
                ),
                highlight_bullet="Architected and shipped the core outreach agent",
            ),
            RankingItem(
                job_id="job_025",
                match_score=91,
                reasoning=(
                    "Glean's agentic workflow engine aligns with your multi-step agent orchestration experience. "
                    "Your pgvector retrieval work is directly relevant to enterprise search backends."
                ),
                highlight_bullet="Designed a two-stage retrieval system (pgvector for shortlist, GPT-4 for reasoning)",
            ),
            RankingItem(
                job_id="job_002",
                match_score=88,
                reasoning=(
                    "Sarvam AI's LangGraph and RAG stack overlaps heavily with your core skills. "
                    "Your cost-aware LLM routing experience would transfer well to their platform."
                ),
                highlight_bullet="Introduced cost budgeting: per-workspace daily LLM budgets enforced via Redis token buckets",
            ),
        ]
    )
    matches = _build_matches(response, jobs, resume)
    assert len(matches) == 5
    assert matches[0].match_score >= matches[-1].match_score
    assert matches[0].job_id == "job_005"
    finalized = finalize_match(matches[0], resume)
    assert highlight_in_resume(finalized.highlight_bullet, resume)
    print("OK  LLM ranking response builds 5 ordered matches")


async def verify_sse_stream() -> None:
    resume = SAMPLE_RESUME.read_text(encoding="utf-8")
    parsed = ParsedResume(
        raw_text=resume,
        signals=ResumeSignals(years_experience=5, location="Bengaluru, India", skills=["Python"]),
        embedding=[0.1] * 1536,
    )
    shortlist = [
        _sample_job("job_005", "Python Backend Developer", "Mentoria"),
        _sample_job("job_025", "Backend Engineer - Agentic", "Glean"),
        _sample_job("job_002", "AI Engineer", "Sarvam AI"),
        _sample_job("job_019", "AI Full Stack Developer", "Rocketlane"),
        _sample_job("job_015", "Founding Engineer", "stealth"),
        _sample_job("job_003", "Full Stack Developer", "Zepto"),
    ]
    mock_matches = [
        JobMatch(
            job_id=job.id,
            title=job.title,
            company=job.company,
            location=job.location,
            remote=job.remote,
            match_score=95 - index * 3,
            reasoning=(
                f"Strong fit for {job.company} based on your Python and AI agent background. "
                "Your production experience aligns with the role requirements."
            ),
            highlight_bullet="Architected and shipped the core outreach agent",
        )
        for index, job in enumerate(shortlist[:5])
    ]

    session = AsyncMock()
    chunks: list[str] = []
    with (
        patch("app.services.matcher.ingest_resume", AsyncMock(return_value=parsed)),
        patch("app.services.matcher.get_cached_matches", AsyncMock(return_value=None)),
        patch("app.services.matcher.embed_text", AsyncMock(return_value=[0.1] * 1536)),
        patch("app.services.matcher.ensure_job_embeddings", AsyncMock(return_value=25)),
        patch("app.services.matcher.search_similar_jobs", AsyncMock(return_value=shortlist)),
        patch("app.services.matcher.rank_jobs_with_llm", AsyncMock(return_value=mock_matches)),
        patch("app.services.matcher.set_cached_matches", AsyncMock(return_value=True)),
    ):
        async for chunk in stream_job_match(session, resume_text=resume):
            chunks.append(chunk)

    body = "".join(chunks)
    assert "event: status" in body
    assert body.count("event: match") == 5
    assert "event: done" in body
    assert '"stage": "ranking"' in body
    print("OK  SSE stream emits status, 5 matches, and done")


def verify_api_stream_endpoint() -> None:
    from fastapi.testclient import TestClient  # noqa: E402

    from app.main import app  # noqa: E402

    resume = SAMPLE_RESUME.read_text(encoding="utf-8")
    parsed = ParsedResume(
        raw_text=resume,
        signals=ResumeSignals(years_experience=5, location="Bengaluru, India", skills=["Python"]),
        embedding=None,
    )
    shortlist = [
        _sample_job(f"job_00{i}", f"Role {i}", f"Company {i}") for i in range(1, 7)
    ]
    mock_matches = [
        JobMatch(
            job_id=job.id,
            title=job.title,
            company=job.company,
            location=job.location,
            remote=job.remote,
            match_score=90 - i,
            reasoning="Personalized reasoning sentence one. Personalized reasoning sentence two.",
            highlight_bullet="Architected and shipped the core outreach agent",
        )
        for i, job in enumerate(shortlist[:5])
    ]

    client = TestClient(app)
    with (
        patch("app.services.matcher.ingest_resume", AsyncMock(return_value=parsed)),
        patch("app.services.matcher.get_cached_matches", AsyncMock(return_value=None)),
        patch("app.services.matcher.embed_text", AsyncMock(return_value=[0.0] * 1536)),
        patch("app.services.matcher.ensure_job_embeddings", AsyncMock(return_value=0)),
        patch("app.services.matcher.search_similar_jobs", AsyncMock(return_value=shortlist)),
        patch("app.services.matcher.rank_jobs_with_llm", AsyncMock(return_value=mock_matches)),
        patch("app.services.matcher.set_cached_matches", AsyncMock(return_value=True)),
    ):
        response = client.post("/api/match/stream/json", json={"resume_text": resume})

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert response.text.count("event: match") == 5
    print("OK  POST /api/match/stream/json returns SSE with 5 matches")


def main() -> None:
    verify_validation()
    verify_build_matches()
    asyncio.run(verify_sse_stream())
    verify_api_stream_endpoint()
    print("Phase 4 verification passed.")


if __name__ == "__main__":
    main()
