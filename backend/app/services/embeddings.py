from openai import APIError, AsyncOpenAI, OpenAIError

from app.core.config import settings
from app.models.job import EMBEDDING_DIMENSIONS
from app.services.resume_errors import ResumeEmbeddingError

MAX_EMBED_CHARS = 12_000


def _client() -> AsyncOpenAI:
    if not settings.openai_api_key:
        raise ResumeEmbeddingError(
            "OPENAI_API_KEY is not configured. Add it to .env to generate embeddings.",
            "missing_api_key",
        )
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def embed_text(text: str) -> list[float]:
    trimmed = text.strip()[:MAX_EMBED_CHARS]
    if not trimmed:
        raise ResumeEmbeddingError("Cannot embed empty text.", "empty_text")

    try:
        response = await _client().embeddings.create(
            model=settings.openai_embedding_model,
            input=trimmed,
        )
    except (OpenAIError, APIError) as exc:
        raise ResumeEmbeddingError(f"Embedding request failed: {exc}", "openai_error") from exc

    embedding = response.data[0].embedding
    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise ResumeEmbeddingError(
            f"Unexpected embedding size {len(embedding)} (expected {EMBEDDING_DIMENSIONS}).",
            "invalid_embedding_size",
        )
    return embedding
