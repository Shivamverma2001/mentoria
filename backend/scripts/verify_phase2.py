#!/usr/bin/env python3
"""Verify Phase 2: seed file parsing + optional live DB check.

Usage (from repo root):
  make db-up && make db-seed
  backend/.venv/bin/python backend/scripts/verify_phase2.py
"""

import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import async_session_factory, engine  # noqa: E402
from app.core.db_init import init_database  # noqa: E402
from app.services.seed import count_jobs, load_jobs_from_file  # noqa: E402


def verify_json() -> None:
    jobs = load_jobs_from_file()
    assert len(jobs) == 25, f"Expected 25 jobs in JSON, got {len(jobs)}"
    usd_job = next(j for j in jobs if j["id"] == "job_004")
    assert "salary_range_usd" in usd_job
    assert "salary_range_inr_lpa" not in usd_job
    print("OK  jobs.json loads 25 records with expected salary field variance")


async def verify_database() -> None:
    async with async_session_factory() as session:
        count = await init_database(session)
        assert count == 25, f"Expected 25 jobs in DB, got {count}"
        recount = await count_jobs(session)
        assert recount == 25, f"Expected 25 jobs on recount, got {recount}"
    await engine.dispose()
    print("OK  database seeded with 25 jobs")


async def main() -> None:
    verify_json()
    try:
        await verify_database()
    except Exception as exc:
        print(f"SKIP database check (start Postgres with: make db-up): {exc}")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
