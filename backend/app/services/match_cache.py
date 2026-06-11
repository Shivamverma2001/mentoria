import logging

from app.core.config import settings
from app.schemas.match import JobMatch
from app.services.cache import cache_get_json, cache_set_json, match_results_key

logger = logging.getLogger(__name__)


async def get_cached_matches(resume_text: str) -> list[JobMatch] | None:
    key = match_results_key(resume_text)
    payload = await cache_get_json(key)
    if not payload:
        return None

    try:
        matches = [JobMatch.model_validate(item) for item in payload["matches"]]
        logger.info("Match cache HIT for key %s (%s results)", key[:48], len(matches))
        return matches
    except Exception as exc:
        logger.warning("Invalid match cache payload for %s: %s", key, exc)
        return None


async def set_cached_matches(resume_text: str, matches: list[JobMatch]) -> bool:
    key = match_results_key(resume_text)
    payload = {"matches": [match.model_dump() for match in matches]}
    stored = await cache_set_json(key, payload, settings.match_cache_ttl_seconds)
    if stored:
        logger.info("Match cache SET for key %s (TTL %ss)", key[:48], settings.match_cache_ttl_seconds)
    return stored
