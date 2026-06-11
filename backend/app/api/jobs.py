from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.jobs import list_jobs as fetch_jobs
from app.services.seed import count_jobs

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(db: AsyncSession = Depends(get_db)) -> dict:
    jobs = await fetch_jobs(db)
    return {
        "total": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "remote": job.remote,
                "experience_min_years": job.experience_min_years,
                "experience_max_years": job.experience_max_years,
                "salary_range_inr_lpa": job.salary_range_inr_lpa,
                "salary_range_usd": job.salary_range_usd,
                "posted_date": job.posted_date.isoformat(),
                "skills_required": job.skills_required,
                "has_embedding": job.embedding is not None,
            }
            for job in jobs
        ],
    }


@router.get("/count")
async def jobs_count(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    return {"count": await count_jobs(db)}
