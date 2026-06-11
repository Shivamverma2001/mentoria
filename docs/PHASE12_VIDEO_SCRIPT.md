# Phase 12 — Video Walkthrough Script (5–8 min)

Record with **Loom** (recommended) or upload to **Google Drive** (anyone with link can view).  
Target length: **6–7 minutes**. Speak to a reviewer who has not seen the repo.

After recording, paste the link in [README.md](../README.md) under **Walkthrough video**.

---

## Pre-recording checklist

- [ ] `cp .env.example .env` with valid `OPENAI_API_KEY`
- [ ] `docker compose up --build` — UI at http://localhost:3000
- [ ] Close unrelated tabs; 1920×1080 or 1280×720
- [ ] IDE open to proud + rewrite files (tabs below)
- [ ] Optional: Sentry project open for `job_match_completed` event

---

## Script with timestamps

### 0:00–0:30 — Intro

> "Hi, I'm [name]. This is my submission for the Arya Smart Job Matcher take-home.  
> The app takes a resume — paste or PDF — matches it against 25 seeded jobs, and streams the top 5 with personalized reasoning and a cover-letter highlight bullet.  
> Stack: FastAPI, async SQLAlchemy, Postgres with pgvector, Redis, React TypeScript, OpenAI for embeddings and ranking."

Show: README architecture diagram (or live UI homepage).

---

### 0:30–2:30 — Live demo (required)

1. Open **http://localhost:3000**
2. Click **Load sample resume** (Aarav Mehta)
3. Click **Match jobs**
4. Narrate progress stages: parsing → embedding → retrieving → ranking
5. Point out cards appearing **one by one** (not all at once)
6. Expand one card — score, 2–3 line reasoning, highlight bullet
7. Call out expected strong matches: **Mentoria** (`job_005`), **Glean**, **Sarvam**, **Rocketlane**
8. Click **Match jobs** again — mention faster second run (`cache_hit` in done event; optional: DevTools → Network → stream response)

> "Weak roles like the intern posting and the .NET consultancy should not appear in the top 5 — the two-stage pipeline filters those out."

---

### 2:30–4:30 — Architecture choices (required)

Open README **Architecture** section or whiteboard verbally:

| Topic | What to say (30 sec each) |
|-------|---------------------------|
| **Two-stage** | "pgvector shortlists 12 jobs by cosine similarity; GPT-4o-mini reranks to 5 with reasoning. Scales to thousands of JDs without sending everything to the LLM." |
| **OpenAI** | "One provider for embeddings (`text-embedding-3-small`) and ranking (`gpt-4o-mini`). Cheap, fast structured JSON." |
| **LangChain, not LangGraph** | "Single ranking prompt — no multi-agent graph needed. LangChain's `with_structured_output` gives reliable Pydantic parsing." |
| **SSE** | "Server-Sent Events over POST — fetch + ReadableStream on the frontend. One-way stream fits this UX; nginx has buffering disabled." |
| **Redis** | "Three caches: full match results, resume embeddings, job embeddings. Repeat matches skip the LLM." |

Optional: quick flash of `docker compose ps` showing 4 services healthy.

---

### 4:30–5:30 — Proud of (required)

**File:** `backend/app/services/matcher.py`

Show `stream_job_match` — async generator that:

- Yields SSE `status` → `match` → `done` events
- Checks Redis match cache early
- Replays cached results with progress events so UX stays consistent
- Records Sentry metrics on success/failure

**Talking point:**

> "I'm proud of this pipeline as a single async generator — one code path for cache hit and miss, typed SSE events, and observability hooks without blocking the event loop."

Optional second beat: `finalize_match` in `match_validation.py` — fuzzy check that highlight bullets are grounded in resume text.

---

### 5:30–6:30 — Would rewrite (required)

**File:** `backend/app/services/llm_ranker.py` — `_build_matches` fallback block (~lines 155–175)

Show the padding logic when LLM returns fewer than 5 valid jobs.

**Talking point:**

> "If I rewrote one thing, it's this fallback — it pads with generic templated reasoning. I'd replace it with a stricter retry prompt or a smaller second LLM call per missing slot. I'd also stream tokens per job instead of the cosmetic `asyncio.sleep` gaps after one structured LLM response — that's honest in the README known issues."

Alternative rewrite: `resume_ingest` PDF path — swap `pypdf` for layout-aware parsing.

---

### 6:30–7:00 — Wrap-up

> "Repo is public at [GitHub URL]. README has setup, full architecture, one-more-week, and known limitations.  
> Run `docker compose up --build` with an OpenAI key to reproduce. Thanks for watching."

---

## Recording tips

- **Pace:** Demo first (hooks reviewer), then architecture, then code — not the reverse.
- **Don't** read the entire README aloud — hit the five decision bullets.
- **Do** show at least one match card long enough to read reasoning.
- **Length:** If over 8 min, trim architecture table; if under 5 min, extend demo with PDF upload.

---

## After recording

1. Copy share link (Loom or Drive)
2. Update README line: `**Walkthrough video:** https://...`
3. Complete Phase 13 submission email (see [SUBMISSION.md](./SUBMISSION.md))
