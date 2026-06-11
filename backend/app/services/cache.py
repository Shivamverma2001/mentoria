import hashlib
import json
import logging
from typing import Any

from app.core.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

CACHE_VERSION = "v1"


def hash_text(text: str) -> str:
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def match_results_key(resume_text: str) -> str:
    return f"arya:{CACHE_VERSION}:match:{hash_text(resume_text)}"


def resume_embedding_key(resume_text: str) -> str:
    scope = settings.embedding_fingerprint
    return f"arya:{CACHE_VERSION}:resume_emb:{scope}:{hash_text(resume_text)}"


def job_embedding_key(job_id: str, content_hash: str) -> str:
    scope = settings.embedding_fingerprint
    return f"arya:{CACHE_VERSION}:job_emb:{scope}:{job_id}:{content_hash}"


async def cache_get_json(key: str) -> Any | None:
    client = get_redis()
    if client is None:
        return None
    try:
        raw = await client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Redis GET failed for %s: %s", key, exc)
        return None


async def cache_set_json(key: str, value: Any, ttl_seconds: int) -> bool:
    client = get_redis()
    if client is None:
        return False
    try:
        await client.setex(key, ttl_seconds, json.dumps(value))
        return True
    except Exception as exc:
        logger.warning("Redis SET failed for %s: %s", key, exc)
        return False


async def cache_delete(key: str) -> None:
    client = get_redis()
    if client is None:
        return
    try:
        await client.delete(key)
    except Exception as exc:
        logger.warning("Redis DELETE failed for %s: %s", key, exc)
