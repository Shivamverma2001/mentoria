# Arya Smart Job Matcher

Mentoria take-home assignment: match a candidate resume against job descriptions and stream the top 5 results with personalized reasoning.

> **Status:** Phase 0–7 complete (full backend API). Frontend UI and Docker compose polish in progress.

## Quick start

```bash
# 1. Copy env and add your OpenAI + Sentry keys
cp .env.example .env

# 2. Install backend (Python 3.11+)
make backend-install

# 3. Start Postgres + Redis and seed jobs
make db-up          # postgres + redis (requires Docker Desktop)
make db-seed        # loads 25 jobs from backend/data/jobs.json

# 4. Run API
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

# 5. Frontend (separate terminal)
cd frontend && npm install && npm run dev

# Verify
make verify-phase2
make verify-phase3
make verify-phase4
make verify-phase5
make verify-phase6
make verify-phase7
```

**API docs:** [docs/API.md](docs/API.md) · Interactive: http://localhost:8000/docs

## Observability (Sentry)

1. Create a free project at [sentry.io](https://sentry.io) and copy the DSN into `.env` as `SENTRY_DSN`.
2. On each successful match, the backend emits a **`job_match_completed`** event with `duration_ms`, `shortlist_size`, `llm_total_tokens`, `top_score`, and `cache_hit`.
3. Check `/api/health` — `"sentry": "enabled"` when DSN is configured.

## Caching (Redis)

| Cache | TTL (default) | Env var |
|-------|---------------|---------|
| Match results (top 5 + reasoning) | 1 hour | `MATCH_CACHE_TTL_SECONDS` |
| Resume embeddings | 24 hours | `RESUME_EMBEDDING_CACHE_TTL_SECONDS` |
| Job embeddings | 7 days | `JOB_EMBEDDING_CACHE_TTL_SECONDS` |

Repeat the same resume match within TTL → faster response, `cache_hit: true` in the `done` SSE event.


- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/api/health
- Jobs list: http://localhost:8000/api/jobs
- Job count: http://localhost:8000/api/jobs/count
- Resume ingest (paste JSON): `POST /api/resume/ingest/json` with `{"resume_text":"...", "embed": false}`
- Resume ingest (form): `POST /api/resume/ingest` with `resume_text` or `resume_file` (PDF)
- **Job match (SSE):** `POST /api/match/stream/json` with `{"resume_text":"..."}` — streams top 5 matches

## Project layout

```
mentoria/
├── backend/           # FastAPI + async SQLAlchemy
│   ├── app/
│   └── data/          # jobs.json + sample resume
├── frontend/          # React + TypeScript + Tailwind
├── docs/
│   └── PHASE0_PLAN.md # Architecture decisions (draft)
└── docker-compose.yml # Phase 9
```

## Architecture

See [docs/PHASE0_PLAN.md](docs/PHASE0_PLAN.md) for the full design doc draft. Summary:

- **Two-stage matching:** pgvector shortlist (12) → OpenAI gpt-4o-mini rerank (top 5)
- **Streaming:** SSE from `POST /api/match/stream`
- **Stack:** FastAPI, async SQLAlchemy, PostgreSQL + pgvector, Redis, Sentry, LangChain (structured output)

Full README sections (setup, one-more-week, known issues) will be completed in Phase 11.

## Sample data

- Jobs: `backend/data/jobs.json` (25 roles)
- Demo resume: `backend/data/sample_resume_aarav_mehta.txt`
