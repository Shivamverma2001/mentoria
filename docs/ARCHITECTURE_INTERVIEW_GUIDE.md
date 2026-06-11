# Architecture & Interview Guide

Complete file-wise and logic-wise walkthrough for your **explanation video** and **technical interviews**.

---

## 1. Elevator pitch (30 seconds)

> "User pastes or uploads a resume. The React app opens an SSE stream to FastAPI. The backend parses the resume, embeds it, uses **pgvector** to shortlist ~12 similar jobs from Postgres, then calls an **LLM** to pick the **top 5** with scores, reasoning, and a resume highlight. Results stream back as SSE events. **Redis** caches embeddings and full match results. **Sentry** logs match success/failure."

---

## 2. End-to-end flow (click "Match jobs")

```
Browser (React)
    │  POST /api/match/stream/json  { resume_text }
    ▼
nginx (frontend container)  →  proxies /api to backend:8000, buffering OFF
    ▼
api/match.py  →  StreamingResponse(stream_job_match(...))
    ▼
services/matcher.py  ← THE ORCHESTRATOR (async generator, yields SSE chunks)
    │
    ├─ resume_ingest.py     parse PDF/text + extract signals
    ├─ match_cache.py       Redis: full top-5 hit? → replay stream & return
    ├─ embeddings.py        embed resume (OpenAI or Gemini)
    ├─ job_embeddings.py    embed any jobs missing vectors in DB
    ├─ vector_search.py     pgvector cosine → top 12 jobs
    ├─ llm_ranker.py        LLM structured JSON → top 5 ranked
    ├─ match_validation.py  validate/fix highlights & reasoning
    ├─ match_cache.py       store top-5 in Redis
    └─ observability.py     Sentry job_match_completed / failed
    ▼
SSE events back to browser → useJobMatch hook → cards appear one by one
```

---

## 3. Repo map (file by file)

### Root / infra

| File | Role |
|------|------|
| `docker-compose.yml` | Postgres (pgvector), Redis, backend, frontend |
| `.env` | API keys, `LLM_PROVIDER`, TTLs, `SHORTLIST_SIZE` |
| `backend/data/jobs.json` | **Source of truth** for 25 jobs — only used at **seed** time |
| `Makefile` | `db-up`, `verify-phase*`, compose helpers |

### Backend entry & config

| File | Role |
|------|------|
| `backend/app/main.py` | FastAPI app, CORS, Sentry init, lifespan: Redis + DB seed + embedding fingerprint sync |
| `backend/app/core/config.py` | All env settings; `uses_gemini`, `embedding_fingerprint` |
| `backend/app/core/database.py` | Async SQLAlchemy engine + `get_db()` dependency |
| `backend/app/core/redis.py` | Async Redis client; app works if Redis is down |
| `backend/app/core/db_init.py` | `CREATE EXTENSION vector`, `create_all`, seed if empty, HNSW index |
| `backend/app/core/sentry.py` | Optional Sentry SDK |

### API layer (thin — HTTP + wiring only)

| File | Endpoints |
|------|-----------|
| `api/match.py` | `POST /api/match/stream`, `/stream/json` → SSE |
| `api/resume.py` | `POST /api/resume/ingest` — parse only (no full match) |
| `api/jobs.py` | `GET /api/jobs`, `/count`, `/{id}` |
| `api/health.py` | DB + Redis + Sentry status |
| `api/root.py` | `GET /api` index |

### Models & schemas

| File | Role |
|------|------|
| `models/job.py` | `Job` table + `embedding vector(1536)` + `embedding_text()` |
| `schemas/match.py` | `JobMatch`, `StatusEvent`, `DoneEvent`, SSE shapes |
| `schemas/ranking.py` | `RankingResponse` — what the LLM must return |
| `schemas/resume.py` | `ResumeSignals` (years, location, skills) |

### Services (business logic — interview focus)

| File | Role |
|------|------|
| **`services/matcher.py`** | **Main pipeline** — async generator, SSE, cache branch |
| `services/resume_parser.py` | PDF → text (`pypdf`); rejects non-PDF |
| `services/resume_signals.py` | Regex/heuristics: years, location, skills |
| `services/resume_ingest.py` | Combines parse + signals; optional embed |
| `services/embeddings.py` | Single/batch embed; OpenAI **or** Gemini (1536 dims) |
| `services/job_embeddings.py` | Batch-embed jobs missing vectors; save to Postgres |
| `services/vector_search.py` | `ORDER BY cosine_distance LIMIT 12` |
| `services/llm_ranker.py` | LangChain prompt + structured output → 5 matches |
| `services/match_validation.py` | Fuzzy check highlight is from resume |
| `services/match_cache.py` | Redis: cache full top-5 by resume hash |
| `services/cache.py` | Low-level Redis JSON get/set + key naming |
| `services/embedding_fingerprint.py` | On provider change → `UPDATE jobs SET embedding = NULL` |
| `services/seed.py` | Load `jobs.json` → Postgres (runtime never reads JSON) |
| `services/observability.py` | Sentry custom events + metrics |

### Frontend

| File | Role |
|------|------|
| `frontend/src/App.tsx` | UI state: resume text, file, buttons |
| `frontend/src/hooks/useJobMatch.ts` | Phase machine: idle → streaming → done/error |
| `frontend/src/api/matchStream.ts` | `fetch` + `ReadableStream` SSE parser (not EventSource — POST body) |
| `frontend/src/lib/parseSse.ts` | Split `event:` / `data:` blocks |
| `frontend/src/components/ResumeInput.tsx` | Textarea + PDF upload |
| `frontend/src/components/MatchProgress.tsx` | Stage labels from `status` events |
| `frontend/src/components/MatchResults.tsx` | Cards from `match` events |
| `frontend/nginx.conf` | Proxy `/api`, **`proxy_buffering off`** for SSE |

---

## 4. Step-by-step logic (`matcher.py`)

**File:** `backend/app/services/matcher.py` — the heart of the app.

1. `yield status: parsing`
2. `ingest_resume(..., embed=False)` — parse PDF/text + extract signals (no API call yet)
3. `get_cached_matches(resume_text)` — Redis hit? Replay SSE and **return early**
4. `embed_text(resume)` — OpenAI or Gemini → 1536-dim vector
5. `yield status: embedding`
6. `ensure_job_embeddings(session)` — first run embeds all 25 jobs into Postgres
7. `yield status: retrieving`
8. `search_similar_jobs(embedding)` — pgvector top **12**
9. `yield status: ranking`
10. `rank_jobs_with_llm(parsed, shortlist)` — LLM picks **5** with reasoning
11. `set_cached_matches(...)` — store full top-5 in Redis (1h TTL)
12. `yield match` × 5 (small delay between for UX)
13. `yield done` with `duration_ms`, `cache_hit: false`
14. On error → `yield error` + Sentry `job_match_failed`

**Design choices:**

- Parse **before** cache lookup (cache key = hash of normalized resume text)
- Embed **after** cache miss (saves API cost on repeat)
- **Async generator** — same SSE pattern for cache hit and miss
- Small `asyncio.sleep` between match events — cards appear sequentially (LLM already finished)

---

## 5. Two-stage matching

### Stage 1 — Retrieval (cheap, fast)

**File:** `backend/app/services/vector_search.py`

- Resume → 1536-dim vector
- Jobs have vectors in `jobs.embedding`
- SQL: cosine distance, `LIMIT 12` (`SHORTLIST_SIZE`)
- **Why:** Filters 25 → 12 semantically similar jobs without sending everything to the LLM

### Stage 2 — Ranking (expensive, smart)

**File:** `backend/app/services/llm_ranker.py`

- Prompt: full resume + `signals` JSON + 12 jobs JSON
- LangChain `with_structured_output(RankingResponse)` → Pydantic parse
- LLM returns exactly 5: `job_id`, `match_score`, `reasoning`, `highlight_bullet`
- **`match_validation.py`** fixes bad highlights if LLM invented text

**Interview answer:**

> "With 25 jobs I *could* send all to the LLM, but two-stage mirrors production: vector search scales to thousands of JDs; the LLM only sees a shortlist so cost and latency stay bounded. Aarav's resume even describes this pattern at Kindred Labs."

---

## 6. Jobs data flow

```
jobs.json  →  seed.py (startup, if DB empty)  →  Postgres jobs table
                                                      ↓
                                            job_embeddings.py fills vectors
                                                      ↓
                                            vector_search reads DB only
```

**Interview:** "`jobs.json` is seed data. The matcher never reads the file at request time — only Postgres. That's intentional for a real catalog that changes independently of code deploys."

---

## 7. Redis — three caches

| Cache | Key idea | TTL | Saves |
|-------|----------|-----|--------|
| Match results | `hash(resume_text)` → full top 5 JSON | 1h | Skip embed + vector + LLM |
| Resume embedding | per text + provider/model | 24h | Skip embed API |
| Job embedding | per `job_id` + content hash | 7d | Skip re-embedding unchanged JDs |

**Interview:** "Redis is optional — if it's down, matching still works, just slower and more API calls. Health endpoint reports cache status."

---

## 8. Streaming — why SSE?

**Assignment requirement:** progressive results, not one 30s blocking wait.

| Choice | Why |
|--------|-----|
| **SSE** | Server → client only; simpler than WebSocket |
| **POST + fetch stream** | `EventSource` can't POST resume body |
| **nginx `proxy_buffering off`** | Without this, nginx buffers SSE and UI freezes until done |
| **Not true token streaming** | One structured LLM call returns all 5; we stream *events* after |

**Honest line:** "True token-by-token reasoning per job would need multiple LLM calls or a streaming parser — I prioritized reliable structured JSON for exactly 5 ranked results."

### SSE event types

| Event | Payload | When |
|-------|---------|------|
| `status` | `{ "stage": "parsing" \| "embedding" \| "retrieving" \| "ranking" }` | Progress |
| `match` | Full `JobMatch` object | Each of 5 results |
| `done` | `{ "total": 5, "duration_ms": N, "cache_hit": bool }` | Complete |
| `error` | `{ "message": "..." }` | Failure |

---

## 9. LangChain vs LangGraph

| | Decision |
|---|----------|
| **LangChain** | Yes — `ChatPromptTemplate` + `with_structured_output` |
| **LangGraph** | No — single ranking step, no agent loop / tools / state machine |

**Interview:** "This isn't an agent that calls tools in a loop. It's one recruiter-style ranking prompt. LangGraph would add complexity without improving match quality here."

---

## 10. OpenAI vs Gemini

| | OpenAI (default) | Gemini (optional) |
|---|------------------|-------------------|
| Config | `LLM_PROVIDER=openai` | `LLM_PROVIDER=gemini` |
| Embed | `text-embedding-3-small` | `gemini-embedding-001` @ 1536 dims |
| Rank | `gpt-4o-mini` | `gemini-2.5-flash-lite` (or similar) |
| Code | `embeddings.py`, `llm_ranker.py` branch on `settings.uses_gemini` |

**`embedding_fingerprint.py`:** switching provider clears job embeddings so OpenAI vectors aren't mixed with Gemini vectors in pgvector.

---

## 11. Frontend flow

1. **`App.tsx`** — user clicks Match → `startMatch({ resumeText })`
2. **`useJobMatch.ts`** — sets `phase: streaming`, wires handlers
3. **`matchStream.ts`** — `POST /api/match/stream/json`
4. Each SSE event:
   - `status` → update progress label ("Ranking with AI…")
   - `match` → append to `matches` state → new card
   - `done` → show duration + `cache_hit`
   - `error` → red banner

**PDF path:** `streamMatchFromPdf` → `POST /api/match/stream` multipart.

---

## 12. Docker startup

On `docker compose up`:

1. Postgres + Redis become healthy
2. Backend `main.py` lifespan → `init_database()` seeds 25 jobs if empty
3. `sync_embedding_fingerprint()` clears vectors if provider/model changed
4. Frontend nginx serves React build, proxies `/api`
5. First match → `ensure_job_embeddings` embeds all jobs (one-time API cost)

---

## 13. Interview Q&A cheat sheet

### "Walk me through a request."

Parse → cache check → embed resume → ensure job embeddings → pgvector top 12 → LLM top 5 → validate → stream SSE → cache result → Sentry.

### "Why pgvector, not in-memory?"

Assignment requires Postgres + pgvector; persists across restarts; same DB as job metadata; HNSW index for scale story.

### "Why 12 shortlist, not 5 or 25?"

12 gives the LLM enough diversity (weak jobs may appear in vector top 12 but LLM drops them); keeps prompt small. Tunable via `SHORTLIST_SIZE`.

### "How do you prevent hallucinated highlights?"

Prompt says "verbatim from resume"; `highlight_in_resume()` fuzzy-matches; fallback to longest resume bullet.

### "What if LLM returns fewer than 5?"

`llm_ranker._build_matches` pads from shortlist with templated reasoning (known limitation — say you'd replace with stricter retry).

### "Why async SQLAlchemy?"

Match path is I/O bound (DB, Redis, OpenAI/Gemini). Async keeps FastAPI responsive under concurrent requests.

### "Why no Alembic?"

Assignment says skip migrations; `create_all` + seed is enough for 25 static jobs.

### "Why no user auth?"

Assignment explicitly excludes it; demo scope.

### "Why PDF only, not DOCX?"

`pypdf` for PDF is fast to ship; DOCX needs `python-docx` — listed in "one more week" README section.

### "How would this scale?"

More jobs → pgvector HNSW + tune shortlist size; background job to embed new JDs; Redis match cache; rate limiting; queue for LLM calls.

### "What are you proud of?"

`matcher.py` — single async generator, cache hit/miss, SSE, observability in one place.

### "What would you rewrite?"

`llm_ranker` fallback padding; cosmetic SSE delays instead of real token streaming; `pypdf` for complex PDF layouts.

### "Why wasn't Mentoria #1 in your demo?"

Razorpay ranked higher on senior backend breadth — reasonable LLM judgment. Brief cared about excluding weak roles and including AI-heavy fits (Glean, Sarvam, Mentoria all in top 5).

---

## 14. Video structure (screen → files)

| Time | Show | Say |
|------|------|-----|
| 0:00 | UI | Problem: match resume to jobs, stream top 5 |
| 0:30 | Live demo | Load sample → Match → cards stream |
| 2:00 | README architecture diagram | Two-stage: vector → LLM |
| 3:00 | `matcher.py` | Orchestrator + SSE generator |
| 4:00 | `vector_search.py` + `llm_ranker.py` | Stage 1 vs 2 |
| 5:00 | `match_cache.py` | Second match faster (`cache_hit`) |
| 5:30 | `llm_ranker.py` fallback | What I'd rewrite |
| 6:30 | Repo + Docker | One-command run |

---

## 15. Code tabs to open while recording

Minimum path for a code walkthrough:

1. `backend/app/services/matcher.py`
2. `backend/app/services/vector_search.py`
3. `backend/app/services/llm_ranker.py`
4. `frontend/src/hooks/useJobMatch.ts`
5. `frontend/src/api/matchStream.ts`

---

## Related docs

- [README.md](../README.md) — full architecture section
- [PHASE0_PLAN.md](./PHASE0_PLAN.md) — initial decisions
- [PHASE12_VIDEO_SCRIPT.md](./PHASE12_VIDEO_SCRIPT.md) — timed recording script
- [API.md](./API.md) — endpoint reference
