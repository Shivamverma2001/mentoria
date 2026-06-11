from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base, engine
from app.services.seed import count_jobs, seed_jobs


async def init_database(session: AsyncSession) -> int:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    job_count = await count_jobs(session)
    if job_count == 0:
        await seed_jobs(session)
        job_count = await count_jobs(session)

    return job_count
