# Arya Smart Job Matcher

Mentoria take-home assignment: match a candidate resume against job descriptions and stream the top 5 results with personalized reasoning.

> **Status:** Phase 0–1 complete (planning + scaffold). Matching pipeline, DB, and UI wiring in progress.

## Quick start

```bash
# 1. Copy env and add your OpenAI + Sentry keys
cp .env.example .env

# 2. Start stack (Phase 9 — docker-compose coming next)
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/api/health

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
