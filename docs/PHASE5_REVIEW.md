# Phase 5 — Review Log

## Deliverables

| Item | Status | Location |
|------|--------|----------|
| Redis in docker-compose | ✅ | `docker-compose.yml` — `redis:7-alpine` |
| Async Redis client | ✅ | `app/core/redis.py` |
| Lifespan connect/disconnect | ✅ | `app/main.py` |
| Graceful degradation if Redis down | ✅ | Caching skipped, app still runs |
| Match results cache | ✅ | `match_cache.py` — key `sha256(resume)` |
| Resume embedding cache | ✅ | `embeddings.py` |
| Job embedding cache | ✅ | `job_embeddings.py` — per job + content hash |
| Health reports Redis | ✅ | `GET /api/health` → `redis`, `cache_enabled` |
| TTLs documented | ✅ | `.env.example`, README |
| Verification | ✅ | `make verify-phase5` |

---

## Cache strategy

| Cache | Key pattern | TTL | Purpose |
|-------|-------------|-----|---------|
| Match results | `arya:v1:match:{sha256(resume)}` | 1h (`MATCH_CACHE_TTL_SECONDS`) | Skip LLM on repeat demo |
| Resume embedding | `arya:v1:resume_emb:{model}:{hash}` | 24h | Skip OpenAI embed call |
| Job embedding | `arya:v1:job_emb:{model}:{job_id}:{hash}` | 7d | Skip re-embedding static JDs |

On **cache hit**, matcher still streams SSE progress + 5 matches, with `done.cache_hit: true`.

---

## Review pass 1 — gaps found & fixed

| Gap | Fix |
|-----|-----|
| Phase 4 tests broke after matcher refactor | Updated `verify_phase4.py` mocks |
| `cache_enabled` false in health test | Patch `redis_available` in verify script |
| `make db-up` didn't start Redis | `db-up` now starts postgres + redis |

---

## Review pass 2 — checklist audit

| Requirement | Met? |
|-------------|------|
| Redis in compose | ✅ |
| Redis client in FastAPI | ✅ |
| Meaningful cache use | ✅ (3 cache layers) |
| TTL documented | ✅ |

**Live test:**

```bash
make db-up
# Run same match twice — second request should log "Match cache HIT" and return cache_hit: true
curl -N -X POST http://localhost:8000/api/match/stream/json \
  -H "Content-Type: application/json" \
  -d "{\"resume_text\": $(jq -Rs . < backend/data/sample_resume_aarav_mehta.txt)}"
```

---

## Ready for Phase 6

Sentry custom events can include `cache_hit` and `duration_ms` on `job_match_completed`.
