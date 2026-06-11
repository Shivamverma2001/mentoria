# Phase 3 — Review Log

## Deliverables

| Item | Status | Location |
|------|--------|----------|
| Resume paste (API) | ✅ | `POST /api/resume/ingest`, `/ingest/json` |
| PDF upload + text extraction | ✅ | `app/services/resume_parser.py` (pypdf) |
| Empty / invalid validation | ✅ | 400 + `code` field |
| Image-only PDF error | ✅ | `image_only_pdf` code |
| Structured signals | ✅ | `app/services/resume_signals.py` |
| Resume embedding | ✅ | `app/services/embeddings.py` (OpenAI) |
| Raw text preserved | ✅ | `ParsedResume.raw_text` in `resume_ingest.py` |
| Exception handlers | ✅ | `app/main.py` → 400 / 502 |
| Verification script | ✅ | `make verify-phase3` |

---

## Review pass 1 — gaps found & fixed

| Gap | Fix |
|-----|-----|
| Exception handlers registered before `app` existed | Moved handlers below `FastAPI()` creation |
| Resume router not mounted | `app.include_router(resume_router)` |
| No automated tests | `backend/scripts/verify_phase3.py` |
| Embedding failure unclear without API key | `missing_api_key` → HTTP 502 |

---

## Review pass 2 — checklist audit

| Requirement | Met? | Notes |
|-------------|------|-------|
| Paste plain text | ✅ | JSON + form field `resume_text` |
| PDF upload | ✅ | form field `resume_file` |
| Clear error messages | ✅ | `detail` + `code` in JSON body |
| Image-only PDF | ✅ | Tested with blank-page PDF |
| Extract signals | ✅ | years, location, skills (heuristic) |
| Generate embedding | ✅ | `embed=true` (default); optional `false` for dev |
| Raw text for LLM | ✅ | `ParsedResume.raw_text` returned to Phase 4 matcher |

**`ParsedResume` object (internal, Phase 4 input):**

```python
@dataclass
class ParsedResume:
    raw_text: str          # full resume for LLM + highlight grounding
    signals: ResumeSignals # years, location, skills
    embedding: list[float] | None  # 1536-dim vector when embed=True
```

---

## API quick reference

```bash
# Paste (no OpenAI key needed)
curl -s -X POST http://localhost:8000/api/resume/ingest/json \
  -H "Content-Type: application/json" \
  -d '{"resume_text":"'"$(cat backend/data/sample_resume_aarav_mehta.txt | jq -Rs .)"'", "embed": false}'

# With embedding (requires OPENAI_API_KEY in .env)
curl -X POST "http://localhost:8000/api/resume/ingest/json" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{"resume_text": "...", "embed": true}
EOF
```

---

## Ready for Phase 4

`ingest_resume()` and `ParsedResume` are the entry point for the matching pipeline (vector shortlist + LLM rerank + SSE stream).
