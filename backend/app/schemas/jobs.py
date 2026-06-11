from datetime import date

from pydantic import BaseModel, Field


class JobSummary(BaseModel):
    id: str
    title: str
    company: str
    location: str
    remote: str
    experience_min_years: int
    experience_max_years: int
    salary_range_inr_lpa: str | None = None
    salary_range_usd: str | None = None
    posted_date: date
    skills_required: list[str]
    has_embedding: bool


class JobListResponse(BaseModel):
    total: int
    jobs: list[JobSummary]


class JobCountResponse(BaseModel):
    count: int = Field(ge=0)
