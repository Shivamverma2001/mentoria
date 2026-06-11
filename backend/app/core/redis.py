import logging
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None
_redis_available: bool = False


async def init_redis() -> bool:
    global _redis_client, _redis_available

    try:
        client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        await client.ping()
        _redis_client = client
        _redis_available = True
        logger.info("Redis connected at %s", settings.redis_url)
        return True
    except Exception as exc:
        _redis_client = None
        _redis_available = False
        logger.warning("Redis unavailable (caching disabled): %s", exc)
        return False


async def close_redis() -> None:
    global _redis_client, _redis_available

    if _redis_client is not None:
        await _redis_client.aclose()
    _redis_client = None
    _redis_available = False


def redis_available() -> bool:
    return _redis_available and _redis_client is not None


def get_redis() -> aioredis.Redis | None:
    return _redis_client if redis_available() else None


async def ping_redis() -> dict[str, Any]:
    client = get_redis()
    if client is None:
        return {"status": "disconnected"}
    try:
        pong = await client.ping()
        return {"status": "connected", "pong": pong}
    except Exception as exc:
        return {"status": "disconnected", "error": str(exc)}
