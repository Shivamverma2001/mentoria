#!/usr/bin/env python3
"""Verify Phase 6: Sentry integration and custom match events."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.sentry import init_sentry, sentry_enabled  # noqa: E402
from app.services.observability import (  # noqa: E402
    JobMatchMetrics,
    capture_job_match_completed,
    capture_job_match_failed,
)


def verify_sentry_disabled_without_dsn() -> None:
    with patch("app.core.sentry.settings") as mock_settings:
        mock_settings.sentry_dsn = ""
        mock_settings.sentry_environment = "test"
        mock_settings.sentry_traces_sample_rate = 0.0
        assert init_sentry() is False
        assert sentry_enabled() is False
    print("OK  Sentry stays disabled without DSN")


def verify_custom_match_event_payload() -> None:
    captured: dict = {}

    def fake_capture_message(message, level="info"):
        captured["message"] = message
        captured["level"] = level

    mock_scope = MagicMock()
    mock_scope.__enter__ = MagicMock(return_value=mock_scope)
    mock_scope.__exit__ = MagicMock(return_value=False)

    with (
        patch("app.services.observability.sentry_enabled", return_value=True),
        patch("app.services.observability.sentry_sdk.push_scope", return_value=mock_scope),
        patch("app.services.observability.sentry_sdk.capture_message", side_effect=fake_capture_message),
    ):
        capture_job_match_completed(
            JobMatchMetrics(
                duration_ms=1840,
                match_count=5,
                shortlist_size=12,
                top_score=94,
                cache_hit=False,
                jobs_embedded=0,
                llm_total_tokens=512,
                top_job_id="job_005",
            )
        )

    assert captured["message"] == "job_match_completed"
    mock_scope.set_tag.assert_any_call("event_type", "job_match_completed")
    mock_scope.set_tag.assert_any_call("cache_hit", "False")
    mock_scope.set_tag.assert_any_call("top_job_id", "job_005")
    context = mock_scope.set_context.call_args[0][1]
    assert context["duration_ms"] == 1840
    assert context["shortlist_size"] == 12
    assert context["llm_total_tokens"] == 512
    print("OK  job_match_completed custom event payload")


def verify_match_failure_event() -> None:
    with (
        patch("app.services.observability.sentry_enabled", return_value=True),
        patch("app.services.observability.sentry_sdk.push_scope") as mock_scope_mgr,
        patch("app.services.observability.sentry_sdk.capture_message") as mock_capture,
    ):
        scope = MagicMock()
        mock_scope_mgr.return_value.__enter__.return_value = scope
        capture_job_match_failed(code="ranking_failed", message="LLM timeout")

    mock_capture.assert_called_once_with("job_match_failed", level="warning")
    scope.set_tag.assert_any_call("error_code", "ranking_failed")
    print("OK  job_match_failed event on stream errors")


def verify_health_reports_sentry() -> None:
    from fastapi.testclient import TestClient  # noqa: E402

    from app.main import app  # noqa: E402

    client = TestClient(app)
    with (
        patch("app.main.ping_redis", AsyncMock(return_value={"status": "disconnected"})),
        patch("app.main.redis_available", return_value=False),
        patch("app.main.sentry_enabled", return_value=True),
    ):
        response = client.get("/api/health")

    assert response.json()["sentry"] == "enabled"
    print("OK  /api/health reports sentry status")


def main() -> None:
    verify_sentry_disabled_without_dsn()
    verify_custom_match_event_payload()
    verify_match_failure_event()
    verify_health_reports_sentry()
    print("Phase 6 verification passed.")


if __name__ == "__main__":
    main()
