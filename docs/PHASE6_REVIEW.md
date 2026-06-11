# Phase 6 — Review Log

## Deliverables

| Item | Status | Location |
|------|--------|----------|
| Sentry SDK integration | ✅ | `app/core/sentry.py`, `sentry-sdk[fastapi]` |
| FastAPI + Starlette integrations | ✅ | Auto-capture unhandled errors |
| Custom `job_match_completed` event | ✅ | `app/services/observability.py` |
| Custom `job_match_failed` event | ✅ | On matcher stream errors |
| LLM token tracking | ✅ | `RankingOutcome.llm_total_tokens` from LangChain raw response |
| Health reports Sentry | ✅ | `GET /api/health` → `"sentry": "enabled\|disabled"` |
| Verification | ✅ | `make verify-phase6` |

---

## Custom event: `job_match_completed`

Emitted after every successful match stream (including cache hits).

**Tags:** `event_type`, `cache_hit`, `top_job_id`

**Context (`job_match`):**

| Field | Description |
|-------|-------------|
| `duration_ms` | End-to-end stream time |
| `match_count` | Always 5 on success |
| `shortlist_size` | pgvector shortlist size (or cached match count) |
| `top_score` | Highest match score |
| `cache_hit` | Redis match cache used |
| `jobs_embedded` | Jobs embedded this run |
| `llm_total_tokens` | OpenAI tokens for ranking (null on cache hit) |
| `top_job_id` | Best-fit job id |

---

## Setup (reviewer / local)

1. Create a free project at [sentry.io](https://sentry.io)
2. Copy DSN to `.env`:
   ```
   SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
   SENTRY_ENVIRONMENT=development
   ```
3. Run a match — look for **Issues → `job_match_completed`** (message event) in Sentry

Without `SENTRY_DSN`, the app runs normally; observability is disabled.

---

## Review pass 1 — gaps found & fixed

| Gap | Fix |
|-----|-----|
| No LLM token metric | `include_raw=True` on LangChain structured output |
| Phase 4 tests broke on `RankingOutcome` | Updated `verify_phase4.py` mocks |
| Cache-hit matches not reported to Sentry | `_record_success` in cached stream path |
| Failed matches silent in Sentry | `job_match_failed` on stream errors |

---

## Review pass 2 — checklist audit

| Requirement | Met? | Notes |
|-------------|------|-------|
| Sentry integrated | ✅ | |
| Custom event/transaction | ✅ | `job_match_completed` message + context |
| Verify in Sentry UI | ⏳ | Requires user DSN + live match |
| Frontend Sentry | ⏭️ | Optional — skipped |

---

## Ready for Phase 7 / 8

Backend API is complete. Phase 8 can wire frontend to `/api/match/stream` and display `cache_hit` from `done` event.
