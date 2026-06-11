#!/usr/bin/env python3
"""Verify Phase 7: API surface, schemas, CORS, and OpenAPI."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

REQUIRED_PATHS = [
    "/api",
    "/api/health",
    "/api/jobs",
    "/api/jobs/count",
    "/api/jobs/{job_id}",
    "/api/resume/ingest",
    "/api/resume/ingest/json",
    "/api/match/stream",
    "/api/match/stream/json",
]

OPENAPI_SCHEMAS = [
    "HealthResponse",
    "JobListResponse",
    "JobCountResponse",
    "JobSummary",
    "ResumeIngestResponse",
    "ResumeIngestJsonBody",
    "MatchJsonBody",
]

PYDANTIC_SSE_SCHEMAS = [
    "JobMatch",
    "StatusEvent",
    "DoneEvent",
    "ErrorEvent",
]


def verify_openapi_paths() -> None:
    from fastapi.testclient import TestClient  # noqa: E402

    from app.main import app  # noqa: E402

    client = TestClient(app)
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]

    for path in REQUIRED_PATHS:
        assert path in paths, f"Missing OpenAPI path: {path}"

    match_post = paths["/api/match/stream"]["post"]
    assert match_post.get("summary")
    print("OK  OpenAPI lists all required endpoints")


def verify_schema_components() -> None:
    from fastapi.testclient import TestClient  # noqa: E402

    from app import schemas  # noqa: E402
    from app.main import app  # noqa: E402

    client = TestClient(app)
    components = client.get("/openapi.json").json()["components"]["schemas"]

    for name in OPENAPI_SCHEMAS:
        assert name in components, f"Missing OpenAPI schema: {name}"

    for name in PYDANTIC_SSE_SCHEMAS:
        cls = getattr(schemas, name)
        assert "properties" in cls.model_json_schema(), f"Missing JSON schema for {name}"
    print("OK  OpenAPI + Pydantic schemas documented")


def verify_api_index() -> None:
    from fastapi.testclient import TestClient  # noqa: E402

    from app.main import app  # noqa: E402

    client = TestClient(app)
    response = client.get("/api")
    assert response.status_code == 200
    body = response.json()
    assert "match_stream_json" in body["endpoints"]
    print("OK  GET /api index")


def verify_health_response_model() -> None:
    from fastapi.testclient import TestClient  # noqa: E402

    from app.main import app  # noqa: E402

    client = TestClient(app)
    with (
        patch("app.api.health.ping_redis", AsyncMock(return_value={"status": "disconnected"})),
        patch("app.api.health.redis_available", return_value=False),
        patch("app.api.health.sentry_enabled", return_value=False),
    ):
        response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert "sentry" in body
    print("OK  GET /api/health returns HealthResponse shape")


def verify_cors_headers() -> None:
    from fastapi.testclient import TestClient  # noqa: E402

    from app.main import app  # noqa: E402

    client = TestClient(app)
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    print("OK  CORS allows local frontend origin")


def verify_error_response_shape() -> None:
    from fastapi.testclient import TestClient  # noqa: E402

    from app.main import app  # noqa: E402
    from app.schemas.errors import ErrorResponse  # noqa: E402

    client = TestClient(app)
    response = client.post("/api/resume/ingest/json", json={"resume_text": "short"})
    assert response.status_code == 400
    body = ErrorResponse.model_validate(response.json())
    assert body.code == "resume_too_short"
    print("OK  errors return ErrorResponse { detail, code }")


def main() -> None:
    verify_openapi_paths()
    verify_schema_components()
    verify_api_index()
    verify_health_response_model()
    verify_cors_headers()
    verify_error_response_shape()
    print("Phase 7 verification passed.")


if __name__ == "__main__":
    main()
