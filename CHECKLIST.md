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
| LLM provider (OpenAI / Anthropic / Gemini) + README justification | Phase 0, 11 |
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

- [ ] Create GitHub repo (public or shared with reviewer email) — **local git init done; push when ready**
- [x] Choose monorepo layout: `backend/` + `frontend/` + root `docker-compose.yml` (compose in Phase 9)
- [x] Add `.gitignore` (`.env`, `__pycache__`, `node_modules`, `.venv`, etc.)
- [x] Add `.env.example` with all required keys:
  - [x] `DATABASE_URL`
  - [x] `REDIS_URL`
  - [x] `OPENAI_API_KEY` + embedding/LLM model vars
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

## Phase 2 — Database & Data Layer

- [ ] Add PostgreSQL service to `docker-compose.yml`
- [ ] Enable **pgvector** extension in Postgres image/init script
- [ ] Set up **async SQLAlchemy** + async session factory
- [ ] Confirm **all** DB reads/writes use async paths (no sync session leaks)
- [ ] Define `Job` model mapping `jobs.json` fields:
  - [ ] `id`, `title`, `company`, `location`, `remote`
  - [ ] `experience_min_years`, `experience_max_years`
  - [ ] `salary_range_inr_lpa`, `salary_range_usd` (nullable — not every job has both)
  - [ ] `posted_date`, `skills_required` (JSON/array), `description`, `apply_url`
  - [ ] `embedding` vector column (pgvector)
- [ ] Write seed script/command to load all 25 jobs from `jobs.json` into Postgres
- [ ] Run seed on startup or via `make seed` / documented CLI command
- [ ] Verify jobs are queryable (count = 25)

---

## Phase 3 — Resume Ingestion

- [ ] Support **resume paste** (plain text) in API
- [ ] Support **PDF upload** (e.g. `pypdf` / `pdfplumber`) — extract text server-side
- [ ] Validate empty/invalid uploads with clear error messages
- [ ] Return usable error if PDF is image-only / unreadable
- [ ] (Optional but useful) Extract structured signals from resume: skills, years, location preference
- [ ] Generate resume embedding (same model as jobs) for the match session
- [ ] Keep raw resume text available for LLM prompt (needed for highlight bullet grounding)

---

## Phase 4 — Matching Pipeline (Core Logic)

### 4a — Vector retrieval (stage 1)

- [ ] Choose embedding model (e.g. `text-embedding-3-small` or provider equivalent)
- [ ] Build job text for embedding: title + skills + description (consistent format)
- [ ] Embed all jobs (on seed or lazy on first run) and store in pgvector
- [ ] Implement similarity search: resume embedding vs job embeddings
- [ ] Shortlist top N candidates (e.g. 10–15) before LLM — document N in README

### 4b — LLM ranking & explanation (stage 2)

- [ ] Implement with LangChain/LangGraph **or** direct SDK calls — document choice in README
- [ ] Prompt LLM with full resume text + shortlisted job details
- [ ] Return exactly **top 5** ranked jobs (best fit first, worst of the five last)
- [ ] For each match, enforce:
  - [ ] `match_score` (define scale, e.g. 0–100)
  - [ ] `reasoning` — 2–3 lines, **personalized** to this candidate (not generic JD summary)
  - [ ] `highlight_bullet` — one **actual** resume bullet to feature in a cover letter
- [ ] Handle LLM failures gracefully (retry once or fallback message)
- [ ] Ensure output is structured (JSON mode / Pydantic parsing)
- [ ] Validate reasoning length and that highlight bullet appears in resume text (or close paraphrase)

### 4c — Streaming (required — assignment rejects 30s blocking)

- [ ] Expose **streaming endpoint** (SSE or WebSocket) — do **not** rely on a single long `POST` that waits for all 5
- [ ] Stream each of the 5 results as they are ready (e.g. one job card at a time)
- [ ] Send progress events: `started`, `retrieving`, `ranking`, `job_match`, `complete`
- [ ] Frontend shows progressive updates while stream is open
- [ ] Confirm perceived wait is incremental, not one frozen screen until the end

---

## Phase 5 — Caching (Redis)

- [ ] Add Redis to `docker-compose.yml`
- [ ] Connect Redis client in FastAPI app
- [ ] Apply caching in at least one **meaningful** place, e.g.:
  - [ ] Job embeddings cache (avoid re-embedding unchanged jobs)
  - [ ] LLM result cache keyed by `hash(resume_text)` for repeat demos
  - [ ] Rate limit / session state for in-flight match jobs
- [ ] Document what you cache and TTL in README

---

## Phase 6 — Observability (Sentry)

- [ ] Create free-tier Sentry project
- [ ] Integrate Sentry in FastAPI backend
- [ ] Capture at least **one meaningful custom event or transaction**, e.g.:
  - `job_match_completed` with `{duration_ms, shortlist_size, llm_tokens, top_score}`
- [ ] Verify event appears in Sentry during a test match
- [ ] (Optional) Add Sentry to React for frontend errors

---

## Phase 7 — Backend API Summary

- [ ] `POST /api/match/stream` (preferred) or streaming variant — resume input + trigger match
- [ ] Accept resume as `multipart/form-data` (PDF file) or JSON `{ "resume_text": "..." }`
- [ ] `GET /api/jobs` (optional) — list jobs for debugging
- [ ] `GET /api/health` — health check for Docker
- [ ] CORS configured for local frontend
- [ ] Request/response models documented (Pydantic schemas)

---

## Phase 8 — Frontend (React + TypeScript)

- [ ] Resume input: textarea (paste) + file upload (PDF)
- [ ] “Match jobs” button triggers **streaming** match (EventSource / fetch stream / WebSocket)
- [ ] Loading / progress UI while stream is active (not a blank screen for 30s)
- [ ] Results list: exactly 5 job cards, ordered **best → worst**
- [ ] Each card shows: title, company, match score, reasoning, highlight bullet
- [ ] (Nice to have) location, remote, or apply link from job data
- [ ] Error state if stream fails or resume is invalid
- [ ] Plain Tailwind UI is fine — do not over-invest in design

---

## Phase 9 — Docker & Local Run

- [ ] Root `docker-compose.yml` with services:
  - [ ] `postgres` (with pgvector)
  - [ ] `redis`
  - [ ] `backend`
  - [ ] `frontend` (preferred in compose; if dev-only, document clearly in README)
- [ ] Backend waits for Postgres/Redis healthy before starting
- [ ] One-command startup documented, e.g. `docker compose up --build`
- [ ] Seed runs automatically or via documented step
- [ ] README lists every env var and where to get API keys
- [ ] **Fresh-clone test:** new machine / clean clone → `docker compose up` → demo works
- [ ] Full flow: upload Aarav resume → see top 5 stream in

---

## Phase 10 — Sanity Check / Demo Validation

- [ ] Dataset: all 25 jobs loaded; matcher never reads jobs from anywhere other than DB seeded from `jobs.json`
- [ ] Test with `Sample_Resume_Aarav_Mehta` — expect strong matches:
  - [ ] Mentoria Python Backend (`job_005`)
  - [ ] Glean Agentic Workflows (`job_025`)
  - [ ] Sarvam AI (`job_002`)
  - [ ] Rocketlane AI Full Stack (`job_019`)
- [ ] Weak matches should rank low: intern (`job_020`), consultancy (`job_023`)
- [ ] Output quality checks:
  - [ ] Exactly 5 results returned
  - [ ] Ranked best → worst
  - [ ] Each reasoning block is 2–3 lines and mentions the candidate
  - [ ] Each highlight bullet is plausibly from the resume
- [ ] Streaming visible in browser (cards appear one by one)
- [ ] Second run benefits from Redis cache (faster or logged cache hit)
- [ ] Sentry event fires on successful match

---

## Phase 11 — README (Most Important Deliverable)

- [ ] **Setup instructions** — teammate can run locally without guessing (clone → env → compose up → open UI)
- [ ] **Architecture** — design doc style (single most important section):
  - [ ] End-to-end flow diagram or prose (ingest → embed → shortlist → LLM → stream)
  - [ ] Why two-stage retrieval vs full LLM on 25 jobs
  - [ ] LLM provider choice and tradeoffs
  - [ ] LangChain/LangGraph: used or skipped, and why
  - [ ] pgvector vs in-memory (if applicable)
  - [ ] Streaming design (SSE/WebSocket) and why not blocking
  - [ ] Redis caching strategy
  - [ ] Ambiguity decisions (scoring scale, location weighting, PDF parsing, salary field handling, etc.)
- [ ] **If I had one more week** — concrete next steps
- [ ] **Known issues & limitations** — honest list of what you skipped or chose not to fix
- [ ] Link to walkthrough video

---

## Phase 12 — Video Walkthrough (5–8 min max)

- [ ] Record Loom or Google Drive video
- [ ] **Live demo** of the feature in action (paste or upload resume → stream results)
- [ ] Explain **architecture choices and why** you made them
- [ ] Show **one thing in your code you are proud of**
- [ ] Show **one thing you would rewrite** and why
- [ ] Keep total length between 5 and 8 minutes

---

## Phase 13 — Final Submission

- [ ] Push all code to GitHub
- [ ] README complete and accurate (re-run fresh-clone test after last push)
- [ ] Share repo link (public) or grant access to reviewer email
- [ ] Share video link in README or submission message
- [ ] Final security pass: no API keys or `.env` committed; `.env.example` is complete
- [ ] Submission bundle complete: **repo + README + video**

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

You are ready to submit when **all** of these are true:

1. User can **upload or paste** a resume in the React + TypeScript UI
2. Matcher uses **≥ 20 jobs** from `jobs.json` (seeded into Postgres)
3. Exactly **top 5** jobs returned, ranked **best → worst**
4. Each result has **match score**, **2–3 line personalized reasoning**, and **one highlight bullet**
5. Results **stream in** progressively — not one 30-second blocking request
6. Backend stack: **FastAPI**, **async SQLAlchemy**, **PostgreSQL**, **pgvector**
7. **Redis** used meaningfully; **Sentry** captures ≥ 1 custom event/transaction
8. LLM provider chosen and **justified in README**; LangChain/LangGraph decision documented
9. `docker compose up` runs the **whole stack** locally on a fresh clone
10. README has setup, architecture, one-more-week, and known-issues sections
11. **5–8 minute** walkthrough video covers demo, architecture, proud item, and rewrite item
12. GitHub repo is public or shared with the reviewer

---

*Last updated: second-pass review against assignment brief*
