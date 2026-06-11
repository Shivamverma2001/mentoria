# Phase 4 — Review Log

## Deliverables

| Item | Status | Location |
|------|--------|----------|
| Embedding model (text-embedding-3-small) | ✅ | `embeddings.py`, `job_embeddings.py` |
| Job text for embedding | ✅ | `Job.embedding_text()` |
| Batch embed all jobs | ✅ | `ensure_job_embeddings()` on match + startup path |
| pgvector similarity search | ✅ | `vector_search.py` — cosine distance, top N |
| Shortlist size 12 | ✅ | `settings.shortlist_size` |
| LangChain structured ranking | ✅ | `llm_ranker.py` — `ChatOpenAI.with_structured_output` |
| Top 5 ranked matches | ✅ | `_build_matches()` + score sort |
| match_score 0–100 | ✅ | Pydantic `Field(ge=0, le=100)` |
| Personalized reasoning | ✅ | Prompt + `reasoning_is_valid()` |
| Highlight bullet grounding | ✅ | `highlight_in_resume()` + fallback picker |
| LLM retry once | ✅ | 2 attempts in `rank_jobs_with_llm()` |
| SSE streaming endpoint | ✅ | `POST /api/match/stream`, `/stream/json` |
| Progress events | ✅ | `status` → stages: parsing, embedding, retrieving, ranking |
| Match events × 5 | ✅ | `event: match` per job |
| Done event | ✅ | `event: done` with duration_ms |
| HNSW index | ✅ | `db_init.py` + after embedding batch |

---

## Pipeline flow

```
POST /api/match/stream
    → ingest resume (parse + embed)
    → ensure_job_embeddings (batch embed missing jobs)
    → pgvector shortlist (top 12)
    → LangChain LLM rank → top 5 with reasoning
    → SSE: status × 4 → match × 5 → done
```

---

## Review pass 1 — gaps found & fixed

| Gap | Fix |
|-----|-----|
| No job embedding on first match | `ensure_job_embeddings()` in stream |
| HNSW index fails on empty embeddings | try/except + retry after embed batch |
| LLM returns < 5 matches | `_build_matches()` pads from shortlist |
| Hallucinated highlight bullets | `finalize_match()` + `pick_best_resume_bullet()` |
| No JSON match endpoint | `POST /api/match/stream/json` |
| No automated tests | `make verify-phase4` |

---

## Review pass 2 — checklist audit

| Requirement | Met? | Notes |
|-------------|------|-------|
| 4a Vector retrieval | ✅ | pgvector cosine distance |
| 4b LLM ranking | ✅ | LangChain + gpt-4o-mini |
| 4c SSE streaming | ✅ | Not a blocking 30s POST |
| Frontend progressive UI | ⏳ | Phase 8 — backend SSE ready |

**Live test (requires Docker + OpenAI key):**

```bash
make db-up && make db-seed
cd backend && .venv/bin/uvicorn app.main:app --reload

curl -N -X POST http://localhost:8000/api/match/stream/json \
  -H "Content-Type: application/json" \
  -d "{\"resume_text\": $(jq -Rs . < backend/data/sample_resume_aarav_mehta.txt)}"
```

---

## Ready for Phase 5

Redis caching can wrap `rank_jobs_with_llm` results keyed by `sha256(resume_text)`.
