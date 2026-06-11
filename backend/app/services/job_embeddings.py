import logging

from openai import APIError, AsyncOpenAI, OpenAIError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import engine
from app.core.db_init import _ensure_vector_index
from app.models.job import Job
from app.services.embeddings import MAX_EMBED_CHARS
from app.services.resume_errors import ResumeEmbeddingError

logger = logging.getLogger(__name__)


def _client() -> AsyncOpenAI:
    if not settings.openai_api_key:
        raise ResumeEmbeddingError(
            "OPENAI_API_KEY is not configured. Add it to .env to generate embeddings.",
            "missing_api_key",
        )
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def embed_texts_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    trimmed = [text.strip()[:MAX_EMBED_CHARS] for text in texts]
    try:
        response = await _client().embeddings.create(
            model=settings.openai_embedding_model,
            input=trimmed,
        )
    except (OpenAIError, APIError) as exc:
        raise ResumeEmbeddingError(f"Batch embedding failed: {exc}", "openai_error") from exc

    return [item.embedding for item in sorted(response.data, key=lambda row: row.index)]


async def ensure_job_embeddings(session: AsyncSession) -> int:
    result = await session.execute(select(Job).where(Job.embedding.is_(None)).order_by(Job.id))
    missing_jobs = list(result.scalars().all())
    if not missing_jobs:
        return 0

    texts = [job.embedding_text() for job in missing_jobs]
    embeddings = await embed_texts_batch(texts)

    for job, embedding in zip(missing_jobs, embeddings, strict=True):
        job.embedding = embedding

    await session.commit()
    async with engine.begin() as conn:
        await _ensure_vector_index(conn)
    logger.info("Generated embeddings for %s jobs", len(missing_jobs))
    return len(missing_jobs)
