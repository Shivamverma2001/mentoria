# Arya Smart Job Matcher — Build Checklist

Step-by-step progress tracker for the Mentoria take-home assignment.  
Check items off as you go. Estimated order is top-to-bottom, but some backend/frontend steps can run in parallel.

**Deadline:** 48 hours from when the brief was shared.

---

## Requirements Coverage (quick audit before submit)

Use this table to confirm nothing was missed.

| Requirement | Covered in |
|-------------|------------|
| Resume input: PDF upload | Phase 3, 8 |
| Resume input: paste text | Phase 3, 8 |
| ≥ 20 jobs from `jobs.json` (source of truth) | Phase 1–2 |
| Top 5 matches, ranked best → worst | Phase 4b, 8, 10 |
| Per match: score + 2–3 line reasoning + highlight bullet | Phase 4b, 8 |
| React + TypeScript UI | Phase 1, 8 |
| Streaming / progressive results (no 30s blocking) | Phase 4c, 8 |
| FastAPI + async SQLAlchemy + PostgreSQL | Phase 2, 7 |
| LLM provider (OpenAI / Anthropic / Gemini) + README justification | Phase 0, 4, 11 (+ optional Gemini via `LLM_PROVIDER`) |
| LangChain or LangGraph — use or skip with reasoning | Phase 0, 4, 11 |
| pgvector (or justified in-memory alternative) | Phase 2, 4a, 11 |
| Redis (or equivalent), meaningful use | Phase 5, 11 |
| Sentry + ≥ 1 custom event or transaction | Phase 6 |
| `docker-compose.yml` runs full stack locally | Phase 9 |
| README: setup, architecture, one more week, known issues | Phase 11 |
| Video: 5–8 min demo + architecture + proud + rewrite | Phase 12 |
| GitHub repo (public or shared with reviewer email) | Phase 1, 13 |
| Bonus: cloud deploy (Render / Railway / Fly) | Optional |

---

## Do NOT Build (assignment explicitly excludes these)

Stop yourself if you drift here — time is better spent on architecture + streaming.

- [ ] **No** user authentication or user management
- [ ] **No** Alembic / migration tooling (simple `create_all` or init SQL is fine)
- [ ] **No** CI pipeline
- [ ] **No** test coverage targets or large test suites
- [ ] **No** UI polish / design craft beyond plain Tailwind
- [ ] **No** exhaustive edge-case handling beyond a reasonable demo

---

## Phase 0 — Understand & Plan (30–60 min) ✅

- [x] Re-read assignment brief: input, output, streaming UX, tech constraints
- [x] Skim `jobs.json` (25 jobs, satisfies ≥ 20 requirement) — note field inconsistencies:
  - [x] `salary_range_inr_lpa` vs `salary_range_usd` (not all jobs have both)
  - [x] `remote`: `hybrid` / `onsite` / `remote`
  - [x] `experience_min_years` / `experience_max_years` vary widely
- [x] Review `Sample_Resume_Aarav_Mehta.docx` for demo expectations
- [x] Decide architecture in one page (two-stage: vector shortlist → LLM rerank + reasoning)
- [x] Pick LLM provider (OpenAI) — documented in `docs/PHASE0_PLAN.md`
- [x] Decide: LangChain yes, LangGraph no — reasoning documented
- [x] Define API response shape per match:
  - [x] `job_id`, `title`, `company` (for UI)
  - [x] `match_score`
  - [x] `reasoning` (2–3 lines)
  - [x] `highlight_bullet` (quoted from the **actual** resume text, not invented)
- [x] Define streaming approach (SSE) — see `docs/PHASE0_PLAN.md`
- [x] List ambiguities to document in README — see `docs/PHASE0_PLAN.md`

---

## Phase 1 — Repo & Project Scaffold ✅

- [x] Create GitHub repo (public): https://github.com/Shivamverma2001/mentoria
- [x] Choose monorepo layout: `backend/` + `frontend/` + root `docker-compose.yml` (compose in Phase 9)
- [x] Add `.gitignore` (`.env`, `__pycache__`, `node_modules`, `.venv`, etc.)
- [x] Add `.env.example` with all required keys:
  - [x] `DATABASE_URL`
  - [x] `REDIS_URL`
  - [x] `OPENAI_API_KEY` + embedding/LLM model vars
  - [x] `LLM_PROVIDER`, `GEMINI_API_KEY`, Gemini model vars (optional fallback)
  - [x] `SENTRY_DSN`
  - [x] `SHORTLIST_SIZE`, `MATCH_CACHE_TTL_SECONDS`, CORS
- [x] Initialize backend: Python 3.11, FastAPI, uvicorn, `requirements.txt`, health endpoint
- [x] Initialize frontend: React + TypeScript (Vite)
- [x] Add Tailwind CSS v4 via `@tailwindcss/vite`
- [x] Copy `jobs.json` → `backend/data/jobs.json`
- [x] Copy sample resume → `backend/data/` + `frontend/public/sample_resume_aarav_mehta.txt`
- [x] Pydantic schemas (`backend/app/schemas/match.py`) + TS types (`frontend/src/types/match.ts`)
- [x] Stub `README.md` with layout and quick-start

---

## Phase 2 — Database & Data Layer ✅

- [x] Add PostgreSQL service to `docker-compose.yml` (`pgvector/pgvector:pg16`)
- [x] Enable **pgvector** extension in Postgres init script + runtime bootstrap
- [x] Set up **async SQLAlchemy** + async session factory (`app/core/database.py`)
- [x] Confirm **all** DB reads/writes use async paths (`get_db`, `AsyncSession` services)
- [x] Define `Job` model mapping `jobs.json` fields:
  - [x] `id`, `title`, `company`, `location`, `remote`
  - [x] `experience_min_years`, `experience_max_years`
  - [x] `salary_range_inr_lpa`, `salary_range_usd` (nullable)
  - [x] `posted_date`, `skills_required` (ARRAY), `description`, `apply_url`
  - [x] `embedding` vector column (1536 dims, nullable until Phase 4)
- [x] Write seed script/command (`app/services/seed.py`, `python -m app.scripts.seed`, `make db-seed`)
- [x] Run seed on startup when DB empty (`app/core/db_init.py` in lifespan)
- [x] Verify jobs queryable — `GET /api/jobs`, `GET /api/jobs/count`, `make verify-phase2`
- [x] Recreated venv with Python 3.11 (assignment requirement)

---

## Phase 3 — Resume Ingestion ✅

- [x] Support **resume paste** (plain text) in API — `POST /api/resume/ingest` + `/ingest/json`
- [x] Support **PDF upload** (pypdf) — extract text server-side
- [x] Validate empty/invalid uploads with clear error messages (`detail` + `code`)
- [x] Return usable error if PDF is image-only / unreadable (`image_only_pdf`)
- [x] Extract structured signals: skills, years, location (`resume_signals.py`)
- [x] Generate resume embedding (`text-embedding-3-small` or Gemini `gemini-embedding-001`) — `embed=true` default
- [x] Keep raw resume text in `ParsedResume.raw_text` for LLM / highlight grounding
- [x] `make verify-phase3` — automated checks

---

## Phase 4 — Matching Pipeline (Core Logic) ✅

### 4a — Vector retrieval (stage 1)

- [x] Embedding model: OpenAI `text-embedding-3-small` or Gemini `gemini-embedding-001` (1536 dims)
- [x] Job embedding text: title + skills + description (`Job.embedding_text()`)
- [x] Batch embed jobs on first match (`ensure_job_embeddings`)
- [x] pgvector cosine similarity shortlist (`vector_search.py`)
- [x] Shortlist top **12** (`SHORTLIST_SIZE` in `.env`)

### 4b — LLM ranking & explanation (stage 2)

- [x] LangChain structured output (`ChatOpenAI` or `ChatGoogleGenerativeAI` when `LLM_PROVIDER=gemini`) — LangGraph skipped
- [x] Prompt with full resume + shortlisted jobs JSON
- [x] Exactly **top 5**, ranked best → worst
- [x] Per match: `match_score` (0–100), `reasoning`, `highlight_bullet`
- [x] LLM retry once; fallback padding if < 5 results
- [x] Pydantic `RankingResponse` structured output
- [x] Validate reasoning + highlight grounding (`match_validation.py`)
- [x] `make verify-phase4`

### 4c — Streaming (required — assignment rejects 30s blocking)

- [x] `POST /api/match/stream` + `/stream/json` — SSE `text/event-stream`
- [x] Stream 5 `match` events sequentially (50ms stagger for UX)
- [x] Progress `status` events: parsing, embedding, retrieving, ranking
- [x] `done` event with `duration_ms`
- [x] Frontend progressive updates — **Phase 8**

---

## Phase 5 — Caching (Redis) ✅

- [x] Add Redis to `docker-compose.yml` (`redis:7-alpine`, port 6379)
- [x] Connect async Redis client in FastAPI (`app/core/redis.py`, lifespan)
- [x] Meaningful caches implemented:
  - [x] **Match results** — `sha256(resume_text)`, TTL 1h — skips LLM on repeat
  - [x] **Resume embeddings** — TTL 24h — skips OpenAI embed call
  - [x] **Job embeddings** — per `job_id` + content hash, TTL 7d
- [x] Graceful fallback when Redis unavailable (caching disabled, app works)
- [x] `done.cache_hit` flag in SSE stream
- [x] Document TTLs in `.env.example` + README
- [x] `make verify-phase5`

---

## Phase 6 — Observability (Sentry) ✅

- [ ] Create free-tier Sentry project — **user action** (see README / `docs/PHASE6_REVIEW.md`)
- [x] Integrate Sentry in FastAPI backend (`app/core/sentry.py`, init before app)
- [x] Custom event `job_match_completed` with:
  - [x] `duration_ms`, `shortlist_size`, `llm_total_tokens`, `top_score`
  - [x] `cache_hit`, `jobs_embedded`, `top_job_id`, `match_count`
- [x] Custom event `job_match_failed` on stream errors
- [x] `/api/health` reports `sentry: enabled|disabled`
- [x] `make verify-phase6`
- [ ] Verify event in Sentry UI — requires `SENTRY_DSN` in `.env` + live match
- [ ] (Optional) React Sentry — skipped

---

## Phase 7 — Backend API Summary ✅

- [x] `POST /api/match/stream` + `/stream/json` — SSE match stream
- [x] Resume input: `multipart/form-data` (paste/PDF) or JSON `{ "resume_text": "..." }`
- [x] `GET /api/jobs`, `/count`, `/{job_id}` — typed Pydantic responses
- [x] `GET /api/health` — `HealthResponse` (DB, Redis, Sentry)
- [x] `GET /api` — API index
- [x] CORS for `http://localhost:5173` (`BACKEND_CORS_ORIGINS`)
- [x] Pydantic schemas in `app/schemas/` + `docs/API.md` + `/docs`
- [x] `ErrorResponse` on 400/502 errors
- [x] `make verify-phase7`

---

## Phase 8 — Frontend (React + TypeScript) ✅

- [x] Resume input: textarea (paste) + file upload (PDF)
- [x] “Match jobs” triggers **streaming** match (fetch + ReadableStream SSE parser)
- [x] Progress UI with stage labels + match count while stream active
- [x] Results list: job cards appear incrementally, ordered **best → worst**
- [x] Each card: title, company, match score, reasoning, highlight bullet
- [x] Location + remote on cards
- [x] Error state + cancel + clear results
- [x] Load sample resume button
- [x] `make verify-phase8` (vitest + build)

---

## Phase 9 — Docker & Local Run ✅

- [x] Root `docker-compose.yml` with services:
  - [x] `postgres` (pgvector/pg16)
  - [x] `redis` (redis:7-alpine)
  - [x] `backend` (FastAPI, port 8000)
  - [x] `frontend` (nginx, port 3000 → 80)
- [x] Backend waits for Postgres/Redis healthy; frontend waits for backend
- [x] One-command: `docker compose up --build` / `make compose-up`
- [x] Seed on startup via `init_database()` when DB empty
- [x] README env var table + OpenAI/Sentry key sources
- [x] nginx SSE proxy (`proxy_buffering off`)
- [x] `make verify-phase9`
- [x] **Live Docker test** — `docker compose up --build` → UI at localhost:3000 (verified)
- [ ] **Fresh-clone live test** on a second machine (optional sanity check)

---

## Phase 10 — Sanity Check / Demo Validation ✅

- [x] Dataset: 25 jobs; matcher reads DB only (seed from `jobs.json`) — static audit in `verify_phase10`
- [x] Aarav strong matches (heuristic top-12): `job_005`, `job_025`, `job_002`, `job_019`
- [x] Weak match ranks low: `job_023` in bottom 5 (heuristic); `job_020` excluded in mock top-5
- [x] Output quality: 5 results, ranked, reasoning + highlight validators
- [x] SSE incremental events (status + 5 match) — mock + `verify_phase10`
- [x] Sentry `capture_job_match_completed` on success — mock test
- [x] Redis cache `cache_hit: true` on 2nd run — live test when API key + infra up
- [x] `make verify-phase10` + manual browser script in `docs/PHASE10_REVIEW.md`
- [x] Browser streaming UX — Load sample → Match jobs → 5 cards stream (~7.9s)
- [x] Live LLM top-5 quality (Gemini): Glean #2, Sarvam #3, Mentoria #4; weak jobs excluded
- [x] Optional: `LLM_PROVIDER=gemini` + `GEMINI_API_KEY` when OpenAI quota unavailable
- [ ] Rocketlane (`job_019`) in top 5 — nice-to-have (3/4 strong matches achieved)

---

## Phase 11 — README (Most Important Deliverable) ✅

- [x] **Setup instructions** — fresh-clone block: clone → `.env` → `docker compose up` → localhost:3000
- [x] **Architecture** — design doc in README (diagram, two-stage, LLM, LangChain/LangGraph, pgvector, SSE, Redis, ambiguities)
- [x] **If I had one more week** — 7 prioritized concrete items
- [x] **Known issues & limitations** — honest table (LLM latency, no deploy, PDF, fallback matches, etc.)
- [x] Review log: `docs/PHASE11_REVIEW.md`
- [ ] Link to walkthrough video — **Phase 12** (placeholder in README)

---

## Phase 12 — Video Walkthrough (5–8 min max)

- [x] Script with timestamps: `docs/PHASE12_VIDEO_SCRIPT.md`
- [x] Proud code pick: `backend/app/services/matcher.py` (`stream_job_match`)
- [x] Rewrite pick: `backend/app/services/llm_ranker.py` (fallback padding)
- [x] Demo talking points drafted (streaming + top-5 walkthrough)
- [ ] **Record** Loom or Google Drive video (follow `docs/PHASE12_VIDEO_SCRIPT.md`)
- [ ] Paste video link in README + submission email

---

## Phase 13 — Final Submission

- [x] Push code to GitHub (`origin/main`)
- [x] README complete (setup, architecture, submission section)
- [x] Repo link public: https://github.com/Shivamverma2001/mentoria
- [x] Security pass: `.env` gitignored, no keys in repo (`docs/SUBMISSION.md`)
- [x] Submission guide + email template: `docs/SUBMISSION.md`
- [ ] Paste **video link** in README (after Phase 12 recording)
- [x] Live stack tested with Docker + Gemini API key
- [x] Gemini provider support committed (`LLM_PROVIDER=gemini`)
- [ ] Send submission email to reviewer (template in `docs/SUBMISSION.md`)

---

## Optional Bonus (only if core is done)

- [ ] Deploy to Render / Railway / Fly (backend + frontend + managed Postgres)
- [ ] Live URL in README
- [ ] Basic structured logging alongside Sentry

---

## Suggested Time Budget (48h total)

| Phase | Hours |
|-------|-------|
| 0 — Plan | 0.5–1 |
| 1–2 — Scaffold + DB | 3–4 |
| 3–4 — Matching + streaming | 8–12 |
| 5–7 — Redis, Sentry, API | 3–4 |
| 8 — Frontend | 4–6 |
| 9–10 — Docker + validation | 3–4 |
| 11–13 — README + video | 4–6 |
| Buffer / debugging | 6–8 |

---

## Definition of Done

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Upload or paste resume in React + TypeScript UI | ✅ |
| 2 | Matcher uses **≥ 20 jobs** from `jobs.json` (Postgres seed) | ✅ |
| 3 | Exactly **top 5**, ranked best → worst | ✅ |
| 4 | Score + reasoning + highlight bullet per match | ✅ |
| 5 | Results stream progressively (SSE) | ✅ |
| 6 | FastAPI + async SQLAlchemy + PostgreSQL + pgvector | ✅ |
| 7 | Redis meaningful use; Sentry custom events | ✅ (Sentry UI optional) |
| 8 | LLM provider justified in README; LangChain/LangGraph documented | ✅ |
| 9 | `docker compose up` runs full stack locally | ✅ |
| 10 | README: setup, architecture, one-more-week, known issues | ✅ |
| 11 | **5–8 min** walkthrough video | ⏳ Record + link |
| 12 | GitHub repo public | ✅ |

**Remaining before submit:** record video → paste link in README → send email (`docs/SUBMISSION.md`).

---

*Last updated: post live demo (Gemini), browser validation, submission prep*
