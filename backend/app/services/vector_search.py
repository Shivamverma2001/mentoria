from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.job import Job


async def search_similar_jobs(
    session: AsyncSession,
    resume_embedding: list[float],
    limit: int | None = None,
) -> list[Job]:
    shortlist_size = limit or settings.shortlist_size
    distance = Job.embedding.cosine_distance(resume_embedding)

    result = await session.execute(
        select(Job)
        .where(Job.embedding.is_not(None))
        .order_by(distance)
        .limit(shortlist_size)
    )
    return list(result.scalars().all())
