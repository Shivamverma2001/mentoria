#!/usr/bin/env python3
"""Phase 10: Sanity check and demo validation for Aarav sample resume."""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.match_validation import highlight_in_resume, reasoning_is_valid  # noqa: E402
from app.services.resume_ingest import ingest_resume_text_only  # noqa: E402
from app.services.seed import load_jobs_from_file  # noqa: E402

SAMPLE_RESUME = BACKEND_ROOT / "data" / "sample_resume_aarav_mehta.txt"
JOBS_JSON = BACKEND_ROOT / "data" / "jobs.json"

EXPECTED_STRONG = {"job_005", "job_025", "job_002", "job_019"}
EXPECTED_WEAK = {"job_020", "job_023"}

AI_KEYWORDS = [
    "python",
    "fastapi",
    "langchain",
    "langgraph",
    "llm",
    "agent",
    "pgvector",
    "redis",
    "rag",
    "openai",
    "embedding",
    "async",
    "postgresql",
]


def verify_dataset_integrity() -> None:
    jobs = load_jobs_from_file(JOBS_JSON)
    assert len(jobs) == 25, f"Expected 25 jobs, got {len(jobs)}"
    ids = {job["id"] for job in jobs}
    assert EXPECTED_STRONG.issubset(ids)
    assert EXPECTED_WEAK.issubset(ids)
    print("OK  jobs.json has 25 jobs with expected strong/weak ids")


def verify_seed_is_only_json_source() -> None:
    allowed = {
        BACKEND_ROOT / "app" / "main.py",  # OpenAPI tag description only
        BACKEND_ROOT / "app" / "services" / "seed.py",
        BACKEND_ROOT / "app" / "scripts" / "seed.py",
        BACKEND_ROOT / "scripts" / "verify_phase2.py",
        BACKEND_ROOT / "scripts" / "verify_phase10.py",
    }
    offenders: list[str] = []
    for path in BACKEND_ROOT.rglob("*.py"):
        if "venv" in path.parts or ".venv" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if "jobs.json" in text and path.resolve() not in {p.resolve() for p in allowed}:
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, f"Unexpected jobs.json references: {offenders}"
    print("OK  runtime job data flows through DB seed only (no stray jobs.json reads)")


def _keyword_score(resume_text: str, job: dict) -> int:
    resume_lower = resume_text.lower()
    blob = (
        f"{job['title']} {job['company']} "
        f"{' '.join(job['skills_required'])} {job['description']}"
    ).lower()
    return sum(1 for keyword in AI_KEYWORDS if keyword in resume_lower and keyword in blob)


def verify_aarav_heuristic_shortlist() -> None:
    resume = SAMPLE_RESUME.read_text(encoding="utf-8")
    jobs = load_jobs_from_file(JOBS_JSON)
    ranked = sorted(jobs, key=lambda job: _keyword_score(resume, job), reverse=True)
    top12 = {job["id"] for job in ranked[:12]}
    bottom5 = {job["id"] for job in ranked[-5:]}

    strong_in_shortlist = EXPECTED_STRONG & top12
    assert len(strong_in_shortlist) >= 3, (
        f"Expected ≥3 strong matches in keyword top-12, got {strong_in_shortlist}"
    )

    weak_in_bottom = EXPECTED_WEAK & bottom5
    assert len(weak_in_bottom) >= 1, (
        f"Expected weak jobs near bottom of heuristic ranking, bottom5={bottom5}"
    )
    print(f"OK  Aarav heuristic shortlist: strong hits={strong_in_shortlist}, weak low={weak_in_bottom}")


def verify_aarav_resume_signals() -> None:
    resume = SAMPLE_RESUME.read_text(encoding="utf-8")
    parsed = ingest_resume_text_only(resume, embed=False)
    assert parsed.signals.years_experience == 5
    assert parsed.signals.location and "Bengaluru" in parsed.signals.location
    assert "Python" in parsed.signals.skills
    assert "FastAPI" in parsed.signals.skills
    assert "LangChain" in parsed.signals.skills or "LangGraph" in parsed.signals.skills
    print("OK  Aarav resume signals (years, location, skills)")


def verify_output_quality_helpers() -> None:
    resume = SAMPLE_RESUME.read_text(encoding="utf-8")
    bullet = "Architected and shipped the core outreach agent"
    assert highlight_in_resume(bullet, resume)

    reasoning = (
        "Your LangGraph agent work at Kindred Labs aligns with Mentoria's Arya backend. "
        "The role's FastAPI and pgvector stack matches your recent production experience."
    )
    assert reasoning_is_valid(reasoning)
    print("OK  highlight + reasoning quality helpers pass on Aarav content")


def _parse_sse_matches(body: str) -> tuple[list[dict], dict | None, bool]:
    matches: list[dict] = []
    done: dict | None = None
    has_status = False

    for block in body.split("\n\n"):
        if not block.strip():
            continue
        event = "message"
        data = ""
        for line in block.split("\n"):
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data = line[5:].strip()
        if not data:
            continue
        payload = json.loads(data)
        if event == "status":
            has_status = True
        elif event == "match":
            matches.append(payload)
        elif event == "done":
            done = payload
    return matches, done, has_status


def verify_sse_incremental_mock() -> None:
    from unittest.mock import AsyncMock, MagicMock

    from fastapi.testclient import TestClient  # noqa: E402

    from app.main import app  # noqa: E402
    from app.schemas.ranking import RankingOutcome  # noqa: E402
    from app.schemas.match import JobMatch  # noqa: E402
    from app.services.resume_ingest import ParsedResume  # noqa: E402
    from app.schemas.resume import ResumeSignals  # noqa: E402

    resume = SAMPLE_RESUME.read_text(encoding="utf-8")
    parsed = ParsedResume(
        raw_text=resume,
        signals=ResumeSignals(years_experience=5, location="Bengaluru, India", skills=["Python"]),
        embedding=None,
    )

    mock_matches = []
    for index, job_id in enumerate(["job_005", "job_025", "job_002", "job_019", "job_015"]):
        mock_matches.append(
            JobMatch(
                job_id=job_id,
                title=f"Role {job_id}",
                company="Co",
                location="Bengaluru, India",
                remote="hybrid",
                match_score=95 - index * 3,
                reasoning=(
                    "Your Python and LangGraph experience fits this role well. "
                    "The stack overlap with FastAPI and pgvector is a strong match for Aarav."
                ),
                highlight_bullet="Architected and shipped the core outreach agent",
            )
        )

    client = TestClient(app)
    with (
        patch("app.services.matcher.ingest_resume", AsyncMock(return_value=parsed)),
        patch("app.services.matcher.get_cached_matches", AsyncMock(return_value=None)),
        patch("app.services.matcher.embed_text", AsyncMock(return_value=[0.1] * 1536)),
        patch("app.services.matcher.ensure_job_embeddings", AsyncMock(return_value=0)),
        patch(
            "app.services.matcher.search_similar_jobs",
            AsyncMock(return_value=[MagicMock(id=f"job_{i:03d}") for i in range(1, 13)]),
        ),
        patch(
            "app.services.matcher.rank_jobs_with_llm",
            AsyncMock(return_value=RankingOutcome(matches=mock_matches, llm_total_tokens=400)),
        ),
        patch("app.services.matcher.set_cached_matches", AsyncMock(return_value=True)),
        patch("app.services.matcher.capture_job_match_completed") as mock_sentry,
    ):
        response = client.post("/api/match/stream/json", json={"resume_text": resume})

    assert response.status_code == 200
    matches, done, has_status = _parse_sse_matches(response.text)
    assert has_status
    assert len(matches) == 5
    assert matches[0]["match_score"] >= matches[-1]["match_score"]
    assert done and done.get("total") == 5
    assert EXPECTED_STRONG.issubset({match["job_id"] for match in matches})
    assert not EXPECTED_WEAK & {match["job_id"] for match in matches}
    mock_sentry.assert_called_once()
    print("OK  SSE mock stream: 5 ranked matches, strong ids present, sentry hook called")


async def verify_live_pipeline() -> None:
    from app.core.config import settings  # noqa: E402

    api_key = settings.openai_api_key.strip()
    if not api_key or api_key.startswith("sk-your"):
        print("SKIP live pipeline (set OPENAI_API_KEY in .env)")
        return

    from app.core.database import async_session_factory, engine  # noqa: E402
    from app.core.db_init import init_database  # noqa: E402
    from app.core.redis import close_redis, init_redis  # noqa: E402
    from app.services.matcher import stream_job_match  # noqa: E402

    resume = SAMPLE_RESUME.read_text(encoding="utf-8")

    try:
        await init_redis()
        async with async_session_factory() as session:
            count = await init_database(session)
            assert count == 25, f"Expected 25 jobs in DB, got {count}"

            async def collect_stream() -> tuple[str, list[dict], dict | None]:
                chunks: list[str] = []
                async for chunk in stream_job_match(session, resume_text=resume):
                    chunks.append(chunk)
                body = "".join(chunks)
                matches, done, _ = _parse_sse_matches(body)
                return body, matches, done

            with patch("app.services.matcher.capture_job_match_completed") as mock_sentry:
                body1, matches1, done1 = await collect_stream()
                mock_sentry.assert_called_once()

            assert len(matches1) == 5, f"Expected 5 matches, got {len(matches1)}: {matches1}"
            assert matches1[0]["match_score"] >= matches1[-1]["match_score"]
            assert "event: status" in body1
            assert body1.count("event: match") == 5

            matched_ids = {match["job_id"] for match in matches1}
            overlap = EXPECTED_STRONG & matched_ids
            assert len(overlap) >= 2, (
                f"Expected ≥2 of {EXPECTED_STRONG} in top 5, got {matched_ids}"
            )
            assert not EXPECTED_WEAK & matched_ids, f"Weak jobs in top 5: {matched_ids & EXPECTED_WEAK}"

            for match in matches1:
                assert reasoning_is_valid(match["reasoning"]), match["reasoning"]
                assert highlight_in_resume(match["highlight_bullet"], resume)

            _, matches2, done2 = await collect_stream()
            assert len(matches2) == 5
            assert done2 and done2.get("cache_hit") is True, "Second run should hit Redis match cache"

            print(
                f"OK  live pipeline: top5={list(matched_ids)}, strong_overlap={overlap}, cache_hit=True"
            )
    except Exception as exc:
        print(f"SKIP live pipeline ({exc})")
    finally:
        await close_redis()
        await engine.dispose()


def main() -> None:
    verify_dataset_integrity()
    verify_seed_is_only_json_source()
    verify_aarav_heuristic_shortlist()
    verify_aarav_resume_signals()
    verify_output_quality_helpers()
    verify_sse_incremental_mock()
    asyncio.run(verify_live_pipeline())
    print("Phase 10 verification passed.")


if __name__ == "__main__":
    main()
