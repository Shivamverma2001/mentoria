# Phase 11 — Review Log

## Deliverable: README architecture section

Primary location: [README.md](../README.md) — sections **Architecture**, **If I had one more week**, **Known issues & limitations**.

---

## Checklist coverage

| Requirement | Status | Location |
|-------------|--------|----------|
| Setup: clone → env → compose → UI | ✅ | README “Setup (fresh clone)” + Docker quick start |
| End-to-end flow diagram | ✅ | ASCII diagram + numbered steps |
| Two-stage vs full LLM | ✅ | Table + rationale |
| LLM provider + tradeoffs | ✅ | OpenAI table + alternatives |
| LangChain / LangGraph | ✅ | Used vs skipped with reasoning |
| pgvector vs in-memory | ✅ | Decision + why in-memory rejected |
| SSE streaming design | ✅ | Events table + nginx + fetch parser |
| Redis caching | ✅ | Three-cache table with TTLs |
| Ambiguity decisions | ✅ | Scoring, location, salary, PDF, highlights, etc. |
| One more week | ✅ | 7 concrete items, prioritized |
| Known issues | ✅ | Honest limitations table |
| Video link | ⏳ | Placeholder — Phase 12 |

---

## Review pass 1

- Architecture reflects **actual code** (`matcher.py`, `llm_ranker.py`, `cache.py`, `match_validation.py`).
- Two-stage shortlist size (12) matches `SHORTLIST_SIZE` default.
- Cache TTLs match `.env.example`.
- SSE cosmetic delays on cache hit documented honestly in known issues.
- LLM fallback padding documented in ambiguities + known issues.

---

## Review pass 2

| Check | Result |
|-------|--------|
| Teammate can run without guessing | ✅ Fresh-clone block at top |
| Design doc tone (not just file list) | ✅ Tradeoff tables, rationale |
| No overclaiming (streaming = post-LLM) | ✅ Known issues call this out |
| Links to API.md and phase docs | ✅ Further reading section |
| Status line updated | ✅ Phase 0–11 |

---

## Remaining for submission

- Phase 12: Record 5–8 min video; paste link in README
- Phase 13: Push to GitHub, fresh-clone test, security pass
- Optional: Replace video placeholder; deploy live URL
