# Cloud Deployment (Render + Neon + Upstash)

Deploy the full stack without managing servers. **Render** hosts backend + frontend; **Neon** provides Postgres with **pgvector**; **Upstash** provides Redis.

> Render's managed Postgres does **not** include pgvector — use Neon for the database.

---

## Architecture (cloud)

```
mentoria-ui.onrender.com  (static React)
        │  VITE_API_BASE_URL
        ▼
mentoria-api.onrender.com  (FastAPI Docker)
        ├── Neon Postgres (pgvector)
        ├── Upstash Redis
        └── Gemini / OpenAI API
```

---

## 1. Neon Postgres (pgvector)

1. Create a project at [neon.tech](https://neon.tech)
2. Copy the connection string (starts with `postgresql://`)
3. Convert for async SQLAlchemy:
   ```text
   postgresql+asyncpg://USER:PASS@HOST/DB?sslmode=require
   ```
   Replace `postgresql://` with `postgresql+asyncpg://` and add `?sslmode=require` if missing.
4. In Neon SQL editor, run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
   (The app also runs this on startup.)

---

## 2. Upstash Redis

1. Create a database at [upstash.com](https://upstash.com)
2. Copy the **Redis URL** (`rediss://...` — TLS is fine)

---

## 3. API key

Set either:

- `LLM_PROVIDER=gemini` + `GEMINI_API_KEY` (recommended — free tier), or
- `LLM_PROVIDER=openai` + `OPENAI_API_KEY`

---

## 4. Deploy to Render

### Option A — Blueprint (recommended)

1. Push this repo to GitHub
2. Go to [dashboard.render.com/blueprints](https://dashboard.render.com/blueprints)
3. **New Blueprint Instance** → connect repo
4. Render reads `render.yaml` and creates `mentoria-api` + `mentoria-ui`
5. Set **sync: false** secrets in the Render dashboard:

| Service | Variable | Value |
|---------|----------|-------|
| `mentoria-api` | `DATABASE_URL` | Neon async URL |
| `mentoria-api` | `REDIS_URL` | Upstash URL |
| `mentoria-api` | `GEMINI_API_KEY` | Your key |
| `mentoria-api` | `BACKEND_CORS_ORIGINS` | `https://mentoria-ui.onrender.com` (your UI URL) |

6. Deploy. First API request may be slow (cold start on free tier).

### Option B — Manual

**Backend (Web Service → Docker)**

- Root directory: `backend`
- Dockerfile path: `Dockerfile`
- Health check: `/api/health`
- Env: `DATABASE_URL`, `REDIS_URL`, `GEMINI_API_KEY`, `LOG_JSON=true`, `BACKEND_CORS_ORIGINS`

**Frontend (Static Site)**

- Root directory: `frontend`
- Build: `npm ci && npm run build`
- Publish: `dist`
- Env: `VITE_API_BASE_URL=https://YOUR-API.onrender.com`
- Rewrite rule: `/*` → `/index.html`

---

## 5. Verify deployment

```bash
curl https://mentoria-api.onrender.com/api/health
curl https://mentoria-api.onrender.com/api/jobs/count
```

Open `https://mentoria-ui.onrender.com` → Load sample resume → Match jobs.

---

## 6. Live URL in README

After deploy, update README:

```markdown
**Live demo:** https://mentoria-ui.onrender.com
**API:** https://mentoria-api.onrender.com/docs
```

---

## Structured logging

Production sets `LOG_JSON=true`. Logs are JSON lines on stdout (visible in Render logs):

```json
{
  "timestamp": "2026-06-11T12:00:00+00:00",
  "level": "INFO",
  "logger": "app.services.matcher",
  "message": "job_match_stream_complete",
  "event": "job_match_stream_complete",
  "match_count": 5,
  "duration_ms": 7896,
  "cache_hit": false,
  "request_id": "uuid-here"
}
```

Each HTTP request gets an `X-Request-ID` header. Sentry remains optional via `SENTRY_DSN`.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| CORS error in browser | Set `BACKEND_CORS_ORIGINS` to exact frontend URL (https, no trailing slash) |
| `vector` extension error | Run `CREATE EXTENSION vector` in Neon SQL editor |
| API 502 on match | Check `GEMINI_API_KEY` / billing; read Render logs |
| Cold start 30–60s | Free tier spins down; first request wakes service |
| Frontend calls wrong API | Rebuild UI after setting `VITE_API_BASE_URL` |

---

## Railway / Fly (alternatives)

Same env vars apply:

- **Railway:** Deploy `backend/Dockerfile` + static frontend; attach Neon + Upstash as plugins or external URLs.
- **Fly.io:** `fly launch` in `backend/`; use Fly Postgres or external Neon; deploy frontend to Fly machines or Cloudflare Pages.

`render.yaml` is the reference; adapt env vars to your platform.
