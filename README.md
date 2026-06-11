# Arya Smart Job Matcher

Mentoria take-home assignment: match a candidate resume against job descriptions and stream the top 5 results with personalized reasoning.

> **Status:** Phase 0–3 complete (through resume ingestion). Matching pipeline and UI wiring in progress.

## Quick start

```bash
# 1. Copy env and add your OpenAI + Sentry keys
cp .env.example .env

# 2. Install backend (Python 3.11+)
make backend-install

# 3. Start Postgres + pgvector and seed jobs
make db-up          # requires Docker Desktop running
make db-seed        # loads 25 jobs from backend/data/jobs.json

# 4. Run API
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

# 5. Frontend (separate terminal)
cd frontend && npm install && npm run dev

# Verify
make verify-phase2
make verify-phase3
```

- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/api/health
- Jobs list: http://localhost:8000/api/jobs
- Job count: http://localhost:8000/api/jobs/count
- Resume ingest (paste JSON): `POST /api/resume/ingest/json` with `{"resume_text":"...", "embed": false}`
- Resume ingest (form): `POST /api/resume/ingest` with `resume_text` or `resume_file` (PDF)

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
