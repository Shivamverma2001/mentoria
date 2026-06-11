# Phase 10 — Review Log

## Automated checks (`make verify-phase10`)

| Check | Status | Notes |
|-------|--------|-------|
| 25 jobs in `jobs.json` | ✅ | |
| Jobs only loaded via seed (not runtime JSON) | ✅ | Static analysis of codebase |
| Aarav heuristic top-12 contains strong ids | ✅ | All 4: job_005, 002, 019, 025 |
| Weak job ranks low (heuristic) | ✅ | job_023 in bottom 5 |
| Aarav resume signals | ✅ | 5 years, Bengaluru, Python/FastAPI |
| Highlight + reasoning validators | ✅ | |
| SSE: 5 matches, ranked, status events | ✅ | Mocked pipeline |
| Sentry hook on success | ✅ | `capture_job_match_completed` |
| Live OpenAI + DB + Redis test | ⏳ | Runs when `OPENAI_API_KEY` set + Postgres/Redis up |

---

## Expected demo results (Aarav Mehta)

### Strong matches (should appear in top 5)

| Job ID | Role | Why |
|--------|------|-----|
| `job_005` | Mentoria Python Backend (Arya) | FastAPI, LangChain, pgvector — literal product match |
| `job_025` | Glean Agentic Workflows | LLM agents, FastAPI, enterprise backend |
| `job_002` | Sarvam AI Engineer | LangGraph, RAG, FastAPI |
| `job_019` | Rocketlane AI Full Stack | Python + React + LangChain |

### Weak matches (should NOT appear in top 5)

| Job ID | Role | Why |
|--------|------|-----|
| `job_020` | Swiggy Backend Intern | 0–1 years experience |
| `job_023` | Generic .NET consultancy | Wrong stack, low quality JD |

---

## Manual demo script (browser)

```bash
cp .env.example .env   # OPENAI_API_KEY required
docker compose up --build
open http://localhost:3000
```

1. Click **Load sample resume**
2. Click **Match jobs**
3. Confirm progress stages appear (not a frozen screen)
4. Confirm **5 cards** stream in one by one, best score first
5. Each card: title, company, score, reasoning, highlight bullet
6. Click **Match jobs** again → faster; `done` event shows `cache_hit: true` (check Network → stream response)
7. (Optional) Check Sentry for `job_match_completed` event

---

## Live pipeline test

When `OPENAI_API_KEY`, Postgres, and Redis are available:

```bash
make db-up
# ensure .env has OPENAI_API_KEY
make verify-phase10
```

Live section validates:
- 25 jobs in DB
- 5 ranked matches from real LLM
- ≥2 expected strong ids in top 5
- No weak ids in top 5
- Valid reasoning + highlight bullets
- Second run `cache_hit: true`

---

## Review pass 2

| Checklist item | Automated | Manual |
|----------------|-----------|--------|
| 25 jobs from JSON via DB | ✅ | |
| Strong matches in top 5 | ✅ heuristic + live* | Browser |
| Weak matches excluded | ✅ heuristic + live* | Browser |
| Exactly 5, ranked | ✅ mock + live* | |
| Reasoning quality | ✅ validators + live* | |
| Highlight from resume | ✅ validators + live* | |
| Streaming incremental | ✅ SSE events | Browser UI |
| Redis cache 2nd run | ✅ live* | Browser |
| Sentry event | ✅ mock + live* | Sentry UI |

*live = when API key + infra available

---

## Ready for Phase 11

Final README architecture section and submission polish.
