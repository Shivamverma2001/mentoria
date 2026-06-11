import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import engine
from app.core.db_init import _ensure_vector_index
from app.models.job import Job
from app.services.cache import cache_get_json, cache_set_json, hash_text, job_embedding_key
from app.services.embeddings import embed_texts_batch
from app.services.resume_errors import ResumeEmbeddingError

logger = logging.getLogger(__name__)


async def _resolve_job_embeddings(jobs: list[Job]) -> list[list[float]]:
    embeddings: list[list[float] | None] = [None] * len(jobs)
    api_indices: list[int] = []
    api_texts: list[str] = []

    for index, job in enumerate(jobs):
        text = job.embedding_text()
        content_hash = hash_text(text)[:16]
        cache_key = job_embedding_key(job.id, content_hash)
        cached = await cache_get_json(cache_key)
        if cached is not None:
            embeddings[index] = cached
            continue
        api_indices.append(index)
        api_texts.append(text)

    if api_texts:
        fetched = await embed_texts_batch(api_texts)
        for job_index, embedding in zip(api_indices, fetched, strict=True):
            embeddings[job_index] = embedding
            job = jobs[job_index]
            content_hash = hash_text(job.embedding_text())[:16]
            await cache_set_json(
                job_embedding_key(job.id, content_hash),
                embedding,
                settings.job_embedding_cache_ttl_seconds,
            )

    if any(embedding is None for embedding in embeddings):
        raise ResumeEmbeddingError("Failed to resolve embeddings for all jobs.", "embedding_resolve_failed")

    return [embedding for embedding in embeddings if embedding is not None]


async def ensure_job_embeddings(session: AsyncSession) -> int:
    result = await session.execute(select(Job).where(Job.embedding.is_(None)).order_by(Job.id))
    missing_jobs = list(result.scalars().all())
    if not missing_jobs:
        return 0

    embeddings = await _resolve_job_embeddings(missing_jobs)

    for job, embedding in zip(missing_jobs, embeddings, strict=True):
        job.embedding = embedding

    await session.commit()
    async with engine.begin() as conn:
        await _ensure_vector_index(conn)
    logger.info("Generated embeddings for %s jobs", len(missing_jobs))
    return len(missing_jobs)
