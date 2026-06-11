from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job


async def list_jobs(session: AsyncSession) -> list[Job]:
    result = await session.execute(select(Job).order_by(Job.id))
    return list(result.scalars().all())


async def get_job_by_id(session: AsyncSession, job_id: str) -> Job | None:
    return await session.get(Job, job_id)
