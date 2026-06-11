from openai import APIError, AsyncOpenAI, OpenAIError

from app.core.config import settings
from app.models.job import EMBEDDING_DIMENSIONS
from app.services.cache import cache_get_json, cache_set_json, resume_embedding_key
from app.services.resume_errors import ResumeEmbeddingError

MAX_EMBED_CHARS = 12_000


def _client() -> AsyncOpenAI:
    if not settings.openai_api_key:
        raise ResumeEmbeddingError(
            "OPENAI_API_KEY is not configured. Add it to .env to generate embeddings.",
            "missing_api_key",
        )
    return AsyncOpenAI(api_key=settings.openai_api_key)


def _validate_embedding(embedding: list[float]) -> list[float]:
    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise ResumeEmbeddingError(
            f"Unexpected embedding size {len(embedding)} (expected {EMBEDDING_DIMENSIONS}).",
            "invalid_embedding_size",
        )
    return embedding


async def embed_text(text: str, *, use_cache: bool = True) -> list[float]:
    trimmed = text.strip()[:MAX_EMBED_CHARS]
    if not trimmed:
        raise ResumeEmbeddingError("Cannot embed empty text.", "empty_text")

    if use_cache:
        cached = await cache_get_json(resume_embedding_key(trimmed))
        if cached is not None:
            return _validate_embedding(cached)

    try:
        response = await _client().embeddings.create(
            model=settings.openai_embedding_model,
            input=trimmed,
        )
    except (OpenAIError, APIError) as exc:
        raise ResumeEmbeddingError(f"Embedding request failed: {exc}", "openai_error") from exc

    embedding = _validate_embedding(response.data[0].embedding)

    if use_cache:
        await cache_set_json(
            resume_embedding_key(trimmed),
            embedding,
            settings.resume_embedding_cache_ttl_seconds,
        )
    return embedding
