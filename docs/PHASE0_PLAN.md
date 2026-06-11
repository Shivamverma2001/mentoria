# Phase 0 — Architecture & Decisions

Planning document for the Arya Smart Job Matcher take-home.  
Decisions here will be expanded into the final README architecture section.

---

## Problem Summary

Given a candidate resume (PDF or pasted text) and 25 jobs from `jobs.json`, return the **top 5** best-fit jobs with:
- match score
- 2–3 line personalized reasoning
- one resume bullet to highlight in a cover letter

Results must **stream progressively** — not a single 30-second blocking response.

---

## High-Level Architecture

```
┌─────────────┐     SSE stream      ┌──────────────────────────────────────────┐
│ React UI    │ ◄────────────────── │ FastAPI Backend                          │
│ paste/PDF   │ ── POST /match ───► │                                          │
└─────────────┘                     │  1. Parse resume (PDF → text)            │
                                    │  2. Embed resume (OpenAI embeddings)     │
                                    │  3. pgvector shortlist (top 12 jobs)     │
                                    │  4. LLM rerank + explain (top 5)         │
                                    │  5. Stream each match via SSE            │
                                    └──────┬───────────────┬───────────────────┘
                                           │               │
                                    ┌──────▼──────┐ ┌──────▼──────┐
                                    │ PostgreSQL  │ │ Redis       │
                                    │ + pgvector  │ │ cache       │
                                    └─────────────┘ └─────────────┘
```

### Two-stage matching (why)

| Stage | What | Why |
|-------|------|-----|
| **1 — Retrieval** | pgvector cosine similarity on job embeddings | Fast, cheap, scales to thousands of JDs; filters noise before LLM |
| **2 — Ranking** | GPT-4o-mini on top 12 shortlist → pick & explain top 5 | LLM adds personalized reasoning and highlight bullets; only 12 jobs in context keeps cost/latency low |

Sending all 25 jobs to the LLM is acceptable for a demo, but two-stage mirrors production Arya patterns and demonstrates cost-aware engineering (see sample resume's Kindred Labs approach).

**Shortlist size:** 12 (documented; tunable constant `SHORTLIST_SIZE`).

---

## LLM Provider: OpenAI

**Choice:** OpenAI (`gpt-4o-mini` for ranking, `text-embedding-3-small` for embeddings)

**Why:**
- Single provider for both embeddings and chat simplifies integration
- `text-embedding-3-small` is fast, cheap, and works well with pgvector (1536 dims)
- `gpt-4o-mini` is strong enough for structured ranking + short reasoning at low cost
- Excellent JSON mode / structured output support
- Well-documented async Python SDK

**Alternatives considered:**
- Anthropic Claude 3.5 Sonnet — better reasoning but separate embedding story (or Voyage)
- Gemini — good but less familiar structured-output ergonomics in Python

---

## Agent Framework: LangChain (light usage)

**Choice:** Use LangChain for structured LLM output chain; **skip LangGraph**.

**Why LangChain helps:**
- `ChatOpenAI` with `.with_structured_output(PydanticModel)` for reliable JSON parsing
- Clean prompt template + chain composition for the ranking step

**Why not LangGraph:**
- Single-step ranking prompt does not need a state machine or multi-agent graph
- LangGraph adds complexity without benefit for this scoped problem

---

## Vector Search: pgvector

**Choice:** pgvector in PostgreSQL (required stack item).

- Store 1536-dim embeddings per job
- Index: IVFFlat or HNSW (HNSW preferred if available in image)
- Query: `ORDER BY embedding <=> :resume_embedding LIMIT 12`

**In-memory alternative rejected:** Assignment prefers pgvector; Postgres is already required.

---

## Streaming: Server-Sent Events (SSE)

**Choice:** `POST /api/match/stream` returns `text/event-stream`.

**Event types:**

| Event | Payload | When |
|-------|---------|------|
| `status` | `{ "stage": "parsing" \| "embedding" \| "retrieving" \| "ranking" }` | Progress updates |
| `match` | `JobMatch` object | Each of 5 results, emitted as ready |
| `done` | `{ "total": 5, "duration_ms": N }` | Stream complete |
| `error` | `{ "message": "..." }` | On failure |

**Why SSE over WebSocket:** One-way server→client fits this use case; simpler than WS; native `EventSource` not usable for POST so frontend uses `fetch` + `ReadableStream` parser.

**Anti-pattern avoided:** Frontend will NOT wait on a single `POST /api/match` that blocks until all 5 are ready.

---

## API Contract

### Request

```
POST /api/match/stream
Content-Type: multipart/form-data  OR  application/json

# Form: resume_file (PDF, optional) + resume_text (optional, at least one required)
# JSON: { "resume_text": "..." }
```

### Match result (per job)

```json
{
  "job_id": "job_005",
  "title": "Python Backend Developer",
  "company": "Mentoria",
  "location": "Mumbai, India",
  "remote": "hybrid",
  "match_score": 92,
  "reasoning": "2–3 lines explaining fit for THIS candidate.",
  "highlight_bullet": "Exact or close quote from the uploaded resume."
}
```

- `match_score`: integer **0–100** (100 = perfect fit)
- `reasoning`: 2–3 sentences, references candidate experience
- `highlight_bullet`: must be grounded in resume text (validated loosely server-side)

### Ranked output

Exactly 5 matches, ordered **best → worst** (highest `match_score` first).

---

## Ambiguity Resolutions (for README)

| Ambiguity | Decision |
|-----------|----------|
| Scoring scale | 0–100 integer, LLM-assigned with rubric in prompt |
| Location / remote preference | Soft signal in LLM prompt only (not hard filter); candidate location parsed from resume if present |
| Salary fields (INR vs USD) | Stored as-is; shown in UI if present; not used in vector search |
| Experience mismatch (e.g. intern role for senior) | LLM penalizes in ranking; vector stage may still surface — LLM filters |
| PDF parsing failures | Return 400 with clear error; no silent fallback |
| jobs.json as source of truth | Seed Postgres on startup from `backend/data/jobs.json`; runtime reads DB only |
| Repeat matches (same resume) | Redis cache keyed by `sha256(resume_text)` → cached top-5 JSON, TTL 1h |
| Highlight bullet hallucination | Prompt instructs quote from resume; post-check that substring overlap exists |

---

## Tech Stack Summary

| Layer | Choice |
|-------|--------|
| Backend | Python 3.11, FastAPI, uvicorn |
| ORM | async SQLAlchemy 2.x |
| Database | PostgreSQL 16 + pgvector |
| Cache | Redis 7 |
| LLM | OpenAI gpt-4o-mini + text-embedding-3-small |
| LLM framework | LangChain (structured output only) |
| Observability | Sentry SDK + custom `job_match_completed` event |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Deploy local | docker-compose.yml (postgres, redis, backend, frontend) |

---

## jobs.json Field Notes

- 25 jobs (≥ 20 required) ✓
- `salary_range_inr_lpa` and `salary_range_usd` are mutually exclusive per job — both nullable in DB
- `remote`: `hybrid` | `onsite` | `remote`
- `skills_required`: string array — included in embedding text
- Low-quality entries (`job_023`) intentionally present — tests ranking quality

---

## Demo Expectations (Aarav Mehta resume)

Strong expected matches: `job_005`, `job_025`, `job_002`, `job_019`  
Weak expected matches: `job_020` (intern), `job_023` (consultancy)

---

## Phase 0 Complete When

- [x] Architecture decided (two-stage)
- [x] LLM provider chosen (OpenAI)
- [x] LangChain/LangGraph decision (LangChain yes, LangGraph no)
- [x] API response shape defined
- [x] Streaming approach defined (SSE)
- [x] Ambiguities documented
