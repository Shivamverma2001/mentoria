from openai import APIError, AsyncOpenAI, OpenAIError

from app.core.config import settings
from app.models.job import EMBEDDING_DIMENSIONS
from app.services.cache import cache_get_json, cache_set_json, resume_embedding_key
from app.services.resume_errors import ResumeEmbeddingError

MAX_EMBED_CHARS = 12_000


def _missing_api_key_error() -> ResumeEmbeddingError:
    return ResumeEmbeddingError(
        f"{settings.api_key_env_name} is not configured. Add it to .env to generate embeddings.",
        "missing_api_key",
    )


def _openai_client() -> AsyncOpenAI:
    if not settings.openai_api_key:
        raise _missing_api_key_error()
    return AsyncOpenAI(api_key=settings.openai_api_key)


def _validate_embedding(embedding: list[float]) -> list[float]:
    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise ResumeEmbeddingError(
            f"Unexpected embedding size {len(embedding)} (expected {EMBEDDING_DIMENSIONS}).",
            "invalid_embedding_size",
        )
    return embedding


async def _embed_openai_batch(texts: list[str]) -> list[list[float]]:
    try:
        response = await _openai_client().embeddings.create(
            model=settings.openai_embedding_model,
            input=texts,
        )
    except (OpenAIError, APIError) as exc:
        raise ResumeEmbeddingError(f"Embedding request failed: {exc}", "openai_error") from exc

    ordered = sorted(response.data, key=lambda row: row.index)
    return [_validate_embedding(item.embedding) for item in ordered]


async def _embed_gemini_batch(texts: list[str]) -> list[list[float]]:
    if not settings.gemini_api_key:
        raise _missing_api_key_error()

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise ResumeEmbeddingError(
            "google-genai package is not installed.",
            "missing_dependency",
        ) from exc

    client = genai.Client(api_key=settings.gemini_api_key)
    try:
        response = await client.aio.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
        )
    except Exception as exc:
        raise ResumeEmbeddingError(f"Gemini embedding request failed: {exc}", "gemini_error") from exc

    if not response.embeddings:
        raise ResumeEmbeddingError("Gemini returned no embeddings.", "gemini_error")

    return [_validate_embedding(list(item.values)) for item in response.embeddings]


async def embed_texts_batch(texts: list[str]) -> list[list[float]]:
    trimmed = [text.strip()[:MAX_EMBED_CHARS] for text in texts]
    if not trimmed or any(not text for text in trimmed):
        raise ResumeEmbeddingError("Cannot embed empty text.", "empty_text")

    if settings.uses_gemini:
        return await _embed_gemini_batch(trimmed)
    return await _embed_openai_batch(trimmed)


async def embed_text(text: str, *, use_cache: bool = True) -> list[float]:
    trimmed = text.strip()[:MAX_EMBED_CHARS]
    if not trimmed:
        raise ResumeEmbeddingError("Cannot embed empty text.", "empty_text")

    if use_cache:
        cached = await cache_get_json(resume_embedding_key(trimmed))
        if cached is not None:
            return _validate_embedding(cached)

    embedding = (await embed_texts_batch([trimmed]))[0]

    if use_cache:
        await cache_set_json(
            resume_embedding_key(trimmed),
            embedding,
            settings.resume_embedding_cache_ttl_seconds,
        )
    return embedding
