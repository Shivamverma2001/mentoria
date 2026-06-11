"""CLI: python -m app.scripts.seed"""

import asyncio

from app.core.database import async_session_factory, engine
from app.core.db_init import init_database
from app.services.seed import count_jobs, seed_jobs


async def main() -> None:
    async with async_session_factory() as session:
        await init_database(session)
        count = await count_jobs(session)
        print(f"Database ready. Jobs in database: {count}")

        # Force re-seed from jobs.json (upsert)
        seeded = await seed_jobs(session)
        count = await count_jobs(session)
        print(f"Seeded/updated {seeded} jobs. Total in database: {count}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
