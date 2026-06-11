from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.jobs import JobCountResponse, JobListResponse, JobSummary
from app.services.jobs import get_job_by_id, list_jobs as fetch_jobs
from app.services.seed import count_jobs

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _to_summary(job) -> JobSummary:
    return JobSummary(
        id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        remote=job.remote,
        experience_min_years=job.experience_min_years,
        experience_max_years=job.experience_max_years,
        salary_range_inr_lpa=job.salary_range_inr_lpa,
        salary_range_usd=job.salary_range_usd,
        posted_date=job.posted_date,
        skills_required=job.skills_required,
        has_embedding=job.embedding is not None,
    )


@router.get("", response_model=JobListResponse, summary="List all jobs")
async def list_jobs(db: AsyncSession = Depends(get_db)) -> JobListResponse:
    jobs = await fetch_jobs(db)
    return JobListResponse(total=len(jobs), jobs=[_to_summary(job) for job in jobs])


@router.get("/count", response_model=JobCountResponse, summary="Count jobs in database")
async def jobs_count(db: AsyncSession = Depends(get_db)) -> JobCountResponse:
    return JobCountResponse(count=await count_jobs(db))


@router.get("/{job_id}", response_model=JobSummary, summary="Get a single job by id")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)) -> JobSummary:
    job = await get_job_by_id(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return _to_summary(job)
