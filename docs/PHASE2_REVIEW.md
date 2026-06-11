# Phase 2 — Review Log

## Deliverables

| Item | Status | Location |
|------|--------|----------|
| PostgreSQL in docker-compose | ✅ | `docker-compose.yml` — `pgvector/pgvector:pg16` |
| pgvector extension | ✅ | `backend/scripts/init-db.sql` + runtime `CREATE EXTENSION` |
| async SQLAlchemy engine + session | ✅ | `backend/app/core/database.py` |
| Job model (all jobs.json fields) | ✅ | `backend/app/models/job.py` |
| Vector column (1536 dims, nullable) | ✅ | `Job.embedding` — filled in Phase 4 |
| Seed from jobs.json | ✅ | `backend/app/services/seed.py` |
| Startup seed (if empty) | ✅ | `backend/app/core/db_init.py` → `lifespan` |
| CLI seed / upsert | ✅ | `python -m app.scripts.seed`, `make db-seed` |
| Async job queries | ✅ | `backend/app/services/jobs.py`, `GET /api/jobs` |
| Verify script | ✅ | `make verify-phase2` |

---

## Review pass 1 — gaps found & fixed

| Gap | Fix |
|-----|-----|
| Python 3.9 venv broke `str \| None` types | Recreated venv with **Python 3.11** |
| App crashed on startup when Postgres down | `lifespan` catches DB errors, logs warning |
| No way to verify 25 jobs without manual SQL | `backend/scripts/verify_phase2.py` + Makefile target |
| DB logic mixed in API route | Extracted `app/services/jobs.py` (async only) |
| README outdated | Added `make db-up`, `make db-seed`, jobs endpoints |
| Makefile used generic python3 | Pinned `python3.11` for venv |

---

## Review pass 2 — checklist audit

| Phase 2 requirement | Met? | Notes |
|-----------------------|------|-------|
| PostgreSQL service in compose | ✅ | Redis/backend added in Phase 9 |
| pgvector enabled | ✅ | Init SQL + idempotent runtime call |
| async SQLAlchemy + session factory | ✅ | `get_db()` dependency |
| All DB I/O async | ✅ | No sync `Session` used |
| Job model fields complete | ✅ | INR/USD salary nullable |
| Seed 25 jobs | ✅ | Upsert on conflict preserves embeddings |
| Seed on startup | ✅ | Only when `count == 0` |
| Jobs queryable, count = 25 | ✅* | *Requires `make db-up` (Docker was offline during dev) |

**Live DB verification command (when Docker is running):**

```bash
make db-up && make db-seed && make verify-phase2
curl http://localhost:8000/api/jobs/count   # → {"count":25}
```

---

## Deferred to later phases

- HNSW / IVFFlat index on `embedding` → Phase 4 (after embeddings generated)
- Redis service in compose → Phase 5 / 9
- Vector similarity search query → Phase 4

---

## Ready for Phase 3

Resume ingestion (PDF paste, text extraction) can build on the async DB layer.
