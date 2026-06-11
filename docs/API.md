# API Reference

Base URL (local): `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

---

## Discovery

### `GET /api`

Returns API name, version, and endpoint index.

---

## Health

### `GET /api/health`

**Response:** `HealthResponse`

| Field | Type | Description |
|-------|------|-------------|
| `status` | `ok` \| `degraded` | Overall health |
| `database` | string | `connected` or `disconnected` |
| `redis` | string | `connected` or `disconnected` |
| `cache_enabled` | bool | Redis cache available |
| `sentry` | `enabled` \| `disabled` | Sentry DSN configured |
| `jobs_count` | int? | Jobs in Postgres |

---

## Jobs

### `GET /api/jobs`

**Response:** `JobListResponse` — all 25 seeded jobs.

### `GET /api/jobs/count`

**Response:** `JobCountResponse` — `{ "count": 25 }`

### `GET /api/jobs/{job_id}`

**Response:** `JobSummary` or 404.

---

## Resume

### `POST /api/resume/ingest`

**Content-Type:** `multipart/form-data`

| Field | Type | Required |
|-------|------|----------|
| `resume_text` | string | One of text or file |
| `resume_file` | PDF file | One of text or file |
| `embed` | bool query | Default `true` |

**Response:** `ResumeIngestResponse`

### `POST /api/resume/ingest/json`

**Body:** `ResumeIngestJsonBody`

```json
{ "resume_text": "...", "embed": false }
```

---

## Match (core feature)

### `POST /api/match/stream`

**Content-Type:** `multipart/form-data`  
**Response:** `text/event-stream` (SSE)

| Field | Type |
|-------|------|
| `resume_text` | string (optional) |
| `resume_file` | PDF (optional) |

### `POST /api/match/stream/json`

**Body:** `MatchJsonBody`

```json
{ "resume_text": "..." }
```

**Response:** SSE stream.

### SSE events

| Event | Schema | Description |
|-------|--------|-------------|
| `status` | `StatusEvent` | `stage`: parsing, embedding, retrieving, ranking |
| `match` | `JobMatch` | One ranked result (×5) |
| `done` | `DoneEvent` | `total`, `duration_ms`, `cache_hit` |
| `error` | `ErrorEvent` | `message` |

### `JobMatch`

```json
{
  "job_id": "job_005",
  "title": "Python Backend Developer",
  "company": "Mentoria",
  "location": "Mumbai, India",
  "remote": "hybrid",
  "match_score": 92,
  "reasoning": "2-3 personalized sentences...",
  "highlight_bullet": "Exact resume bullet to feature..."
}
```

---

## Errors

Structured error body (`ErrorResponse`):

```json
{ "detail": "Human-readable message", "code": "machine_code" }
```

| HTTP | Typical `code` |
|------|----------------|
| 400 | `empty_resume`, `resume_too_short`, `image_only_pdf` |
| 502 | `missing_api_key`, `ranking_failed` |

---

## CORS

Allowed origins from `BACKEND_CORS_ORIGINS` (default `http://localhost:5173`).

---

## Pydantic schema locations

| Schema | File |
|--------|------|
| `JobMatch`, `MatchJsonBody`, SSE events | `backend/app/schemas/match.py` |
| `JobSummary`, `JobListResponse` | `backend/app/schemas/jobs.py` |
| `ResumeIngestResponse` | `backend/app/schemas/resume.py` |
| `HealthResponse` | `backend/app/schemas/health.py` |
| `ErrorResponse` | `backend/app/schemas/errors.py` |
