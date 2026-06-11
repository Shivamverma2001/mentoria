import json
from datetime import date
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job

DEFAULT_JOBS_PATH = Path(__file__).resolve().parents[2] / "data" / "jobs.json"


def _parse_posted_date(value: str) -> date:
    return date.fromisoformat(value)


def load_jobs_from_file(path: Path = DEFAULT_JOBS_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["jobs"]


def job_record_from_dict(raw: dict) -> dict:
    return {
        "id": raw["id"],
        "title": raw["title"],
        "company": raw["company"],
        "location": raw["location"],
        "remote": raw["remote"],
        "experience_min_years": raw["experience_min_years"],
        "experience_max_years": raw["experience_max_years"],
        "salary_range_inr_lpa": raw.get("salary_range_inr_lpa"),
        "salary_range_usd": raw.get("salary_range_usd"),
        "posted_date": _parse_posted_date(raw["posted_date"]),
        "skills_required": raw["skills_required"],
        "description": raw["description"],
        "apply_url": raw["apply_url"],
        "embedding": None,
    }


async def seed_jobs(session: AsyncSession, path: Path = DEFAULT_JOBS_PATH) -> int:
    records = [job_record_from_dict(job) for job in load_jobs_from_file(path)]

    insert_stmt = insert(Job).values(records)
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "title": insert_stmt.excluded.title,
            "company": insert_stmt.excluded.company,
            "location": insert_stmt.excluded.location,
            "remote": insert_stmt.excluded.remote,
            "experience_min_years": insert_stmt.excluded.experience_min_years,
            "experience_max_years": insert_stmt.excluded.experience_max_years,
            "salary_range_inr_lpa": insert_stmt.excluded.salary_range_inr_lpa,
            "salary_range_usd": insert_stmt.excluded.salary_range_usd,
            "posted_date": insert_stmt.excluded.posted_date,
            "skills_required": insert_stmt.excluded.skills_required,
            "description": insert_stmt.excluded.description,
            "apply_url": insert_stmt.excluded.apply_url,
        },
    )
    await session.execute(upsert_stmt)
    await session.commit()
    return len(records)


async def count_jobs(session: AsyncSession) -> int:
    result = await session.scalar(select(func.count()).select_from(Job))
    return int(result or 0)
