import logging

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import get_redis
from app.models.job import Job

logger = logging.getLogger(__name__)

_FINGERPRINT_KEY = "arya:v1:embedding_fingerprint"


async def sync_embedding_fingerprint(session: AsyncSession) -> None:
    """Clear stored job vectors when provider/model changes so jobs get re-embedded."""
    fingerprint = settings.embedding_fingerprint
    client = get_redis()
    if client is None:
        return

    try:
        stored = await client.get(_FINGERPRINT_KEY)
        if stored == fingerprint:
            return

        await session.execute(update(Job).values(embedding=None))
        await session.commit()
        await client.set(_FINGERPRINT_KEY, fingerprint)
        logger.info("Embedding fingerprint changed to %s; cleared job embeddings", fingerprint)
    except Exception as exc:
        logger.warning("Embedding fingerprint sync skipped: %s", exc)
