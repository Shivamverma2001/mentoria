# Arya Smart Job Matcher

Mentoria take-home assignment: match a candidate resume against job descriptions and stream the top 5 results with personalized reasoning.

> **Status:** Phase 0–9 complete (full Docker stack). Submission docs (README architecture, video) in Phase 11–13.

---

## Docker quick start (recommended)

```bash
# 1. Copy env and add your OpenAI API key (required for matching)
cp .env.example .env
# Edit .env → set OPENAI_API_KEY=sk-...

# 2. Start the full stack (Postgres + Redis + backend + frontend)
docker compose up --build
# Or detached: make compose-up-d

# 3. Open the app
# UI:     http://localhost:3000
# API:    http://localhost:8000/docs
# Health: http://localhost:3000/api/health
```

On first startup the backend **auto-seeds 25 jobs** from `backend/data/jobs.json` when the database is empty.

**Demo flow:** Load sample resume → Match jobs → watch 5 results stream in.

```bash
make compose-down   # stop all services
```

---

## Local dev (without Docker frontend)

```bash
cp .env.example .env          # set OPENAI_API_KEY
make backend-install
make db-up                    # postgres + redis only
make db-seed

# Terminal 1
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend && npm install && npm run dev
# http://localhost:5173
```

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | **Yes** (matching) | From [platform.openai.com](https://platform.openai.com/api-keys) |
| `DATABASE_URL` | Auto in Docker | Local: `postgresql+asyncpg://arya:arya@localhost:5432/arya_jobs` |
| `REDIS_URL` | Auto in Docker | Local: `redis://localhost:6379/0` |
| `SENTRY_DSN` | No | From [sentry.io](https://sentry.io) — free tier |
| `SENTRY_ENVIRONMENT` | No | Default `development` |
| `OPENAI_EMBEDDING_MODEL` | No | Default `text-embedding-3-small` |
| `OPENAI_LLM_MODEL` | No | Default `gpt-4o-mini` |
| `BACKEND_CORS_ORIGINS` | No | Comma-separated frontend URLs |
| `SHORTLIST_SIZE` | No | Default `12` |
| `MATCH_CACHE_TTL_SECONDS` | No | Default `3600` |
| `RESUME_EMBEDDING_CACHE_TTL_SECONDS` | No | Default `86400` |
| `JOB_EMBEDDING_CACHE_TTL_SECONDS` | No | Default `604800` |

Docker Compose overrides `DATABASE_URL` and `REDIS_URL` to use internal service hostnames.

---

## Verify

```bash
make verify-phase2   # database seed
make verify-phase3   # resume ingestion
make verify-phase4   # matching + SSE
make verify-phase5   # Redis cache
make verify-phase6   # Sentry
make verify-phase7   # API schemas
make verify-phase8   # frontend build + tests
make verify-phase9   # docker-compose config
```

---

## API & docs

- **API reference:** [docs/API.md](docs/API.md)
- **Interactive docs:** http://localhost:8000/docs
- **Architecture draft:** [docs/PHASE0_PLAN.md](docs/PHASE0_PLAN.md)

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | DB, Redis, Sentry status |
| `GET /api/jobs` | List 25 seeded jobs |
| `POST /api/match/stream/json` | SSE job matching |
| `POST /api/resume/ingest/json` | Parse resume |

---

## Docker services

| Service | Port | Image |
|---------|------|-------|
| frontend | 3000 → 80 | nginx + React build |
| backend | 8000 | FastAPI / uvicorn |
| postgres | 5432 | pgvector/pg16 |
| redis | 6379 | redis:7-alpine |

Backend waits for Postgres + Redis healthchecks. Frontend waits for backend healthcheck. Jobs seed automatically on startup.

---

## Project layout

```
mentoria/
├── backend/            # FastAPI + async SQLAlchemy
├── frontend/           # React + TypeScript + Tailwind
├── docs/               # API.md, phase reviews, architecture
├── docker-compose.yml  # Full stack
└── .env.example
```

---

## Sample data

- Jobs: `backend/data/jobs.json` (25 roles)
- Demo resume: `backend/data/sample_resume_aarav_mehta.txt` (also in UI via Load sample)
