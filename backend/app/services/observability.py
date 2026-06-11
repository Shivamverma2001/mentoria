import logging
from dataclasses import dataclass

import sentry_sdk

from app.core.sentry import sentry_enabled

logger = logging.getLogger(__name__)


@dataclass
class JobMatchMetrics:
    duration_ms: int
    match_count: int
    shortlist_size: int
    top_score: int | None
    cache_hit: bool
    jobs_embedded: int = 0
    llm_total_tokens: int | None = None
    top_job_id: str | None = None


def capture_job_match_completed(metrics: JobMatchMetrics) -> None:
    if not sentry_enabled():
        return

    try:
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("event_type", "job_match_completed")
            scope.set_tag("cache_hit", str(metrics.cache_hit))
            if metrics.top_job_id:
                scope.set_tag("top_job_id", metrics.top_job_id)

            scope.set_context(
                "job_match",
                {
                    "duration_ms": metrics.duration_ms,
                    "match_count": metrics.match_count,
                    "shortlist_size": metrics.shortlist_size,
                    "top_score": metrics.top_score,
                    "cache_hit": metrics.cache_hit,
                    "jobs_embedded": metrics.jobs_embedded,
                    "llm_total_tokens": metrics.llm_total_tokens,
                    "top_job_id": metrics.top_job_id,
                },
            )

            sentry_sdk.capture_message("job_match_completed", level="info")

        logger.debug(
            "Sentry job_match_completed: duration=%sms cache_hit=%s top_score=%s",
            metrics.duration_ms,
            metrics.cache_hit,
            metrics.top_score,
        )
    except Exception as exc:
        logger.warning("Failed to send Sentry job_match_completed event: %s", exc)


def capture_job_match_failed(*, code: str, message: str) -> None:
    if not sentry_enabled():
        return

    try:
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("event_type", "job_match_failed")
            scope.set_tag("error_code", code)
            scope.set_context("job_match_error", {"code": code, "message": message})
            sentry_sdk.capture_message("job_match_failed", level="warning")
    except Exception as exc:
        logger.warning("Failed to send Sentry job_match_failed event: %s", exc)
