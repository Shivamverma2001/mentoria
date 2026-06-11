# Arya Smart Job Matcher

Mentoria take-home assignment: match a candidate resume against job descriptions and stream the top 5 results with personalized reasoning.

> **Status:** Ready to submit — record video (5–8 min), paste link below, send [submission email](docs/SUBMISSION.md).

---

## Setup (fresh clone → running UI)

```bash
git clone <your-repo-url> mentoria && cd mentoria
cp .env.example .env
# Edit .env → set OPENAI_API_KEY=sk-... (required for matching)
docker compose up --build
```

| Step | What happens |
|------|----------------|
| 1 | Postgres + Redis start with healthchecks |
| 2 | Backend waits for DB/Redis, runs migrations, **seeds 25 jobs** from `backend/data/jobs.json` if empty |
| 3 | Frontend (nginx + React build) proxies `/api` to backend |
| 4 | Open **http://localhost:3000** → Load sample resume → Match jobs |

API docs: http://localhost:8000/docs · Health: http://localhost:3000/api/health

**Walkthrough video:** _[Paste your Loom or Google Drive link here after recording]_  
**Recording script:** [docs/PHASE12_VIDEO_SCRIPT.md](docs/PHASE12_VIDEO_SCRIPT.md) (demo, architecture, proud code, rewrite — ~6 min)

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
| `LLM_PROVIDER` | No | `openai` (default) or `gemini` |
| `OPENAI_API_KEY` | **Yes** if `openai` | From [platform.openai.com](https://platform.openai.com/api-keys) |
| `GEMINI_API_KEY` | **Yes** if `gemini` | Free key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `DATABASE_URL` | Auto in Docker | Local: `postgresql+asyncpg://arya:arya@localhost:5432/arya_jobs` |
| `REDIS_URL` | Auto in Docker | Local: `redis://localhost:6379/0` |
| `SENTRY_DSN` | No | From [sentry.io](https://sentry.io) — free tier |
| `SENTRY_ENVIRONMENT` | No | Default `development` |
| `OPENAI_EMBEDDING_MODEL` | No | Default `text-embedding-3-small` |
| `OPENAI_LLM_MODEL` | No | Default `gpt-4o-mini` |
| `GEMINI_EMBEDDING_MODEL` | No | Default `gemini-embedding-001` (1536 dims) |
| `GEMINI_LLM_MODEL` | No | Default `gemini-2.5-flash-lite` |
| `BACKEND_CORS_ORIGINS` | No | Comma-separated frontend URLs |
| `SHORTLIST_SIZE` | No | Default `12` |
| `MATCH_CACHE_TTL_SECONDS` | No | Default `3600` |
| `RESUME_EMBEDDING_CACHE_TTL_SECONDS` | No | Default `86400` |
| `JOB_EMBEDDING_CACHE_TTL_SECONDS` | No | Default `604800` |

Docker Compose overrides `DATABASE_URL` and `REDIS_URL` to use internal service hostnames.

### Using Gemini instead of OpenAI

If OpenAI quota is exhausted, switch providers in `.env`:

```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key-from-aistudio
# OPENAI_API_KEY can be left empty
```

Restart: `docker compose down && docker compose up --build`. Job embeddings are cleared automatically when the provider changes.

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
make verify-phase10  # Aarav demo validation
```

**Demo validation:** `make verify-phase10` checks dataset integrity, Aarav resume signals, expected job rankings (heuristic), and SSE output shape. With `OPENAI_API_KEY` + `make db-up`, it also runs a live match + cache test.

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

---

## Architecture

This section documents **what the system does, why it is built this way, and what tradeoffs were made**. It is the primary design artifact for reviewers.

### End-to-end flow

```
┌──────────────┐   POST /api/match/stream   ┌─────────────────────────────────────────────┐
│ React UI     │ ─────────────────────────► │ FastAPI (async)                             │
│ paste / PDF  │ ◄──── SSE text/event-stream│                                             │
└──────────────┘                            │  1. Parse resume (PDF → text, extract signals)│
                                            │  2. Check Redis match cache (resume hash)     │
                                            │  3. Embed resume (OpenAI, cached in Redis)    │
                                            │  4. Ensure job embeddings in Postgres         │
                                            │  5. pgvector cosine search → top 12 shortlist │
                                            │  6. LLM rerank shortlist → top 5 + reasoning  │
                                            │  7. Stream status → match × 5 → done          │
                                            └──────────┬─────────────────┬──────────────────┘
                                                       │                 │
                                              ┌────────▼────────┐ ┌────▼─────┐
                                              │ PostgreSQL 16   │ │ Redis 7  │
                                              │ + pgvector      │ │ 3 caches │
                                              └─────────────────┘ └──────────┘
```

**Request path** (`backend/app/services/matcher.py`):

1. **Parse** — PDF via `pypdf`, or pasted text. Extract lightweight signals (years of experience, location, skills) for the LLM prompt. No embedding yet.
2. **Match cache lookup** — SHA-256 of normalized resume text → Redis key `arya:v1:match:<hash>`. On hit, replay cached top-5 with synthetic progress events so the UI still feels streamed.
3. **Embed resume** — `text-embedding-3-small` (1536 dims). Cached separately in Redis (24h TTL).
4. **Job embeddings** — On first match after seed, embed all jobs missing vectors. Job text = title + company + skills + description. Per-job Redis cache keyed by content hash (7-day TTL); vectors persisted in Postgres.
5. **Retrieve** — `ORDER BY embedding <=> resume_embedding LIMIT 12` (cosine distance via pgvector).
6. **Rank** — Single LangChain prompt with structured JSON output. GPT-4o-mini picks exactly 5 jobs, assigns 0–100 scores, writes 2–3 line reasoning, and picks a resume highlight bullet.
7. **Validate & stream** — Post-process highlights (fuzzy match against resume lines) and reasoning length. Emit SSE events; small `asyncio.sleep` gaps between matches so cards appear incrementally.

### Why two-stage retrieval (not full LLM on 25 jobs)?

| Approach | Pros | Cons |
|----------|------|------|
| **All 25 → LLM** | Simple; no vector infra | Higher token cost; slower; reasoning quality drops with noisy context |
| **Two-stage (chosen)** | Fast cheap retrieval; LLM only sees 12 relevant jobs | More moving parts; shortlist size is a tuning knob |

With only 25 jobs, sending everything to the LLM would work for a demo. I chose two-stage anyway because:

- It mirrors how production job matchers scale (thousands of JDs, fixed LLM budget).
- Vector search filters obvious mismatches (e.g. .NET consultancy, intern roles) before the LLM spends tokens.
- Latency stays predictable: embedding + pgvector query is ~100ms; the LLM call dominates either way.

**Shortlist size:** 12 (`SHORTLIST_SIZE`). Large enough to include all plausible AI/backend fits for the Aarav demo; small enough to keep the ranking prompt under ~8k tokens.

### LLM provider: OpenAI

| Component | Model | Why |
|-----------|-------|-----|
| Embeddings | `text-embedding-3-small` | Fast, cheap, 1536 dims (native pgvector fit), strong semantic search |
| Ranking | `gpt-4o-mini` | Reliable structured JSON, good reasoning at low cost, async Python SDK |

**Alternatives considered:**

- **Anthropic Claude** — Stronger prose, but needs a separate embedding provider (Voyage, etc.) and adds integration surface.
- **Gemini** — Competitive pricing, but structured-output ergonomics in Python are less mature for this use case.
- **Local / open models** — No API key dependency, but weaker at following “exactly 5 ranked JSON objects with grounded bullets” without more guardrail code.

**Tradeoff accepted:** Vendor lock-in to OpenAI for both embedding and chat. Acceptable for a take-home; production would abstract behind an interface.

### LangChain vs LangGraph

| | Decision |
|---|----------|
| **LangChain** | **Used** — `ChatOpenAI.with_structured_output(RankingResponse)` + `ChatPromptTemplate`. One chain, one LLM call. Handles Pydantic parsing and retries cleanly. |
| **LangGraph** | **Skipped** — Ranking is a single prompt, not a multi-step agent graph. A state machine would add files and complexity without improving match quality. |

The assignment mentions LangGraph; this problem is intentionally **not** agentic — no tool calls, no loops, no human-in-the-loop. A recruiter-style ranking prompt is the right abstraction.

### pgvector vs in-memory vectors

**Choice:** pgvector in PostgreSQL (required by brief).

- Job embeddings stored in `jobs.embedding` (`vector(1536)`).
- Query: SQLAlchemy `Job.embedding.cosine_distance(resume_embedding)` with `LIMIT 12`.
- HNSW index created on startup when missing (`db_init._ensure_vector_index`).

**In-memory rejected:** Does not persist across restarts, does not demonstrate the required Postgres + pgvector stack, and does not compose with SQLAlchemy job metadata.

For 25 jobs, brute-force cosine in Python would be instant — pgvector is about **correct architecture**, not raw speed at this scale.

### Streaming: SSE, not blocking JSON

**Endpoint:** `POST /api/match/stream` (multipart PDF) and `/stream/json` (JSON body).

**Event types:**

| Event | Payload | Purpose |
|-------|---------|---------|
| `status` | `{ "stage": "parsing" \| "embedding" \| "retrieving" \| "ranking" }` | Progress bar in UI |
| `match` | Full `JobMatch` object | One card at a time |
| `done` | `{ "total": 5, "duration_ms": N, "cache_hit": bool }` | Stream complete |
| `error` | `{ "message": "..." }` | Failures (missing API key, no jobs, LLM error) |

**Why SSE over WebSocket:** Server → client only. No bidirectional channel needed. SSE works through nginx (`proxy_buffering off` in `frontend/nginx.conf`).

**Why not a blocking `POST /api/match`:** The brief requires progressive results. A 15–30s spinner with one JSON blob fails the UX requirement. Even on cache hit, the backend replays status + match events with short delays so the UI behavior is consistent.

**Frontend:** `fetch()` + `ReadableStream` parser (`frontend/src/api/matchStream.ts`) — native `EventSource` cannot POST a resume body.

### Redis caching strategy

Three independent caches, all keyed with `arya:v1:` prefix and SHA-256 of normalized text:

| Cache | Key pattern | TTL | What it saves |
|-------|-------------|-----|---------------|
| **Match results** | `match:<resume_hash>` | 1 hour | Full top-5 JSON — skips embed + vector + LLM on repeat |
| **Resume embedding** | `resume_emb:<model>:<hash>` | 24 hours | OpenAI embedding API call |
| **Job embedding** | `job_emb:<model>:<job_id>:<content_hash>` | 7 days | OpenAI embedding API call per job |

Redis is **optional at runtime** — if unavailable, matching still works (cache helpers return `None` / `False`). Health endpoint reports Redis status.

**Cache invalidation:** TTL-based only. Editing `jobs.json` requires re-seeding or clearing Redis manually. Acceptable for a static 25-job dataset.

### Ambiguity decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| **Score scale** | 0–100 integer, LLM-assigned | Rubric in system prompt; sorted descending before stream |
| **Location / remote** | Soft signal in LLM prompt only | No hard geo filter — candidate may relocate; remote preference inferred from resume |
| **Salary (INR vs USD)** | Stored and displayed; **not** used in matching | Fields are mutually exclusive per job; normalizing INR/USD fairly needs more product spec |
| **Experience mismatch** | LLM penalizes; vector may still surface | e.g. intern role in shortlist → LLM should rank it last or exclude from top 5 |
| **PDF parse failure** | HTTP 400 with clear error | No silent fallback to empty resume |
| **jobs.json at runtime** | Seed Postgres on startup; matcher reads **DB only** | Verified by `verify_phase10` static audit |
| **Highlight hallucination** | Prompt says “verbatim from resume”; server runs fuzzy substring check (`match_validation.py`) | Falls back to longest resume bullet if LLM invents text |
| **LLM returns < 5 jobs** | Pad from shortlist with templated fallback reasoning | Rare; prevents broken UI; logged on retry path |

### Observability (Sentry)

Custom events on match completion and failure (`job_match_completed`, `job_match_failed`) with duration, shortlist size, top score, cache hit, and token usage. Sentry is optional — app runs without `SENTRY_DSN`.

### Expected demo behavior (Aarav Mehta resume)

| Category | Job IDs | Roles |
|----------|---------|-------|
| **Strong** (expect in top 5) | `job_005`, `job_025`, `job_002`, `job_019` | Mentoria, Glean, Sarvam, Rocketlane |
| **Weak** (expect excluded) | `job_020`, `job_023` | Swiggy intern, .NET consultancy |

Run `make verify-phase10` for automated checks. Full LLM quality requires `OPENAI_API_KEY` + `make db-up`.

---

## If I had one more week

Concrete next steps, in priority order:

1. **Evaluation harness** — Golden set of 5–10 resumes with expected top-5 job IDs; CI job that runs heuristic + optional live LLM regression on PRs.
2. **Deploy to Render/Railway** — Managed Postgres + Redis + backend; static frontend on CDN; live URL in README for reviewers.
3. **Smarter shortlisting** — Hybrid score: `0.7 × cosine + 0.3 × keyword overlap` on skills/years; hard-filter jobs where `experience_max < candidate_years - 2`.
4. **True incremental LLM streaming** — Stream partial reasoning per job as tokens arrive (today all 5 arrive after one structured LLM call; SSE gaps are cosmetic).
5. **PDF quality** — `pdfplumber` or layout-aware parser for multi-column resumes; OCR fallback for scanned PDFs.
6. **Auth + rate limiting** — API key per user, Redis sliding-window limiter on `/match/stream` to protect OpenAI spend.
7. **Structured logging** — JSON logs with `request_id`, `cache_hit`, `duration_ms` alongside Sentry for local debugging.

---

## Known issues & limitations

Honest list of what was deprioritized or left imperfect:

| Area | Limitation |
|------|------------|
| **LLM latency** | Ranking is one blocking LLM call (~3–8s). SSE `match` events are emitted after ranking completes (small delays are for UX, not token streaming). |
| **No cloud deploy** | Local Docker only unless you add Render/Railway (optional bonus). |
| **Cache invalidation** | TTL-only; no event-driven invalidation when jobs change. |
| **PDF parsing** | Basic `pypdf` text extraction; complex layouts, tables, and scanned PDFs may garble text. |
| **Highlight validation** | Fuzzy match (72% sequence ratio), not strict verbatim — good enough to catch hallucinations, not a legal quote guarantee. |
| **Fallback matches** | If LLM returns fewer than 5 valid jobs, server pads from shortlist with generic reasoning. |
| **No user accounts** | Stateless; no match history, no saved resumes. |
| **Salary ignored in ranking** | Display-only; no cost-of-living or comp-fit logic. |
| **Single-region jobs** | India-focused dataset; no visa/relocation modeling. |
| **Tests** | Phase verify scripts + frontend unit tests; no full E2E Playwright suite against live OpenAI. |
| **Video** | Walkthrough not recorded yet (Phase 12). |

---

## Submission

| Deliverable | Link |
|-------------|------|
| **Repository** | https://github.com/Shivamverma2001/mentoria |
| **Walkthrough video** | _Add Loom/Drive URL above after recording_ |
| **Submission checklist** | [docs/SUBMISSION.md](docs/SUBMISSION.md) |

Email template and fresh-clone test steps are in `docs/SUBMISSION.md`.

---

## Further reading

- [docs/API.md](docs/API.md) — endpoint reference
- [docs/PHASE0_PLAN.md](docs/PHASE0_PLAN.md) — initial architecture decisions
- [docs/PHASE10_REVIEW.md](docs/PHASE10_REVIEW.md) — demo validation checklist
- [docs/PHASE12_VIDEO_SCRIPT.md](docs/PHASE12_VIDEO_SCRIPT.md) — video walkthrough script
