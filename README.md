# Harsh & Enzo — Talent Reconnaissance

A public demo for recruiters: two AI agents (**Harsh**, the field scout, and **Enzo**, the
analyst) sweep LinkedIn for jobs matching a structured recruiter brief, evaluate every
posting against the criteria with an LLM, and stream ranked matches live — narrated
in character.

```
recruiter form ──► LLM builds boolean query + relaxation ladder + eval rubric
                        │
                        ▼
       LinkedIn guest search (24h → 48h → 72h, then 2 relaxed query rungs)
                        │
                        ▼
       per-job: scrape posting ──► LLM verdict ──► SSE events to the browser
                        │
                        ▼
       rank by recency ──► cached in Redis (24h TTL) ── nothing persists longer
```

## Stack

| Piece | Choice |
|---|---|
| Frontend | React 18 + Vite + TypeScript, plain CSS — deploys to **Vercel** |
| Backend | FastAPI + Playwright (headless Chromium) — deploys to **Render** via Dockerfile |
| State | **Upstash Redis** only (rate limits + 24h result cache). No database. |
| LLM | OpenCode gateway (OpenAI-compatible), key server-side only |
| Live progress | Server-Sent Events with replay-on-reconnect |

## Model routing

Two roles, routed independently via env vars:

- **`QUERY_MODEL`** (default `deepseek-v4.1-flash`) — builds the boolean query, the
  2-rung relaxation ladder, and the eval rubric in **one templated call**. This is a
  low-stakes structured task; fast and cheap wins.
- **`EVAL_MODEL`** (default `deepseek-v4.1-flash`) — judges each scraped posting. This is
  where structured-JSON accuracy and rubric-following matter most, so point it at the
  strongest model your OpenCode plan routes to (e.g. a Claude or Kimi model id) when
  available. The JSON parser tolerates fences/prose and retries twice, so flash works
  out of the box — a stronger model mainly improves judgment, not reliability.

## Local development

```bash
# Backend (Python 3.10+)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env            # fill in OPENCODE_API_KEY at minimum
set -a; source .env; set +a
uvicorn app.main:app --reload   # http://localhost:8000

# Frontend
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

With `REDIS_URL` unset the backend uses an in-memory store, so no Redis is needed
locally. Rate limits reset on server restart in that mode.

## Deploy

### Backend → Render (free tier)

The repo ships a `render.yaml` Blueprint, so the fastest path is
**Render → New → Blueprint → connect this repo**. It defines the Docker service,
the free plan, the `/api/health` health check, and the full env-var list in one go.
Secrets (`OPENCODE_API_KEY`, `REDIS_URL`) are marked `sync: false`, so Render
prompts you for them during setup instead of storing them in git.

To do it manually instead: **New → Web Service**, connect the repo, and set
**root directory `backend`**. Render builds the `Dockerfile` automatically. The
image is `mcr.microsoft.com/playwright/python`, which ships Chromium + all
headless system deps (a plain Python buildpack will NOT run Chromium; don't
switch to one).

Environment variables:
- `OPENCODE_API_KEY` — **required** (rotate the old key; see security note)
- `REDIS_URL` — the `rediss://` string from your Upstash database
- `ALLOWED_ORIGINS` — your exact Vercel URL, e.g. `https://harsh-and-enzo.vercel.app`
  (comma-separate if you add a custom domain). CORS is a strict whitelist.
- optional: `EVAL_MODEL`, `QUERY_MODEL`, `CONTACT_LINKEDIN`, `CONTACT_EMAIL`

Render injects `PORT`; the Dockerfile honors it.

> **Free-tier caveat:** Render free web services get 512 MB RAM, sleep after
> 15 idle minutes (a cold start takes ~30–60 s), and share 750 instance-hours per
> month per workspace. Headless Chromium is the memory-hungry part of the pipeline;
> if a run OOMs, trim or disable the browser fallback in `scraper.py` — the `httpx`
> guest-API fast path usually succeeds without ever launching Chromium.

### Frontend → Vercel

1. Import the repo, set **root directory `frontend`** (framework preset: Vite).
2. Set `VITE_API_URL` to the Render public URL, e.g. `https://<service>.onrender.com`
   — no trailing slash.
3. After the first deploy, copy the Vercel URL back into the backend's
   `ALLOWED_ORIGINS`.

### Upstash

Create a free Redis database, copy the `rediss://` connection string into `REDIS_URL`.
Keys used: `ratelimit:<ip>` (counter, no expiry — lifetime limit) and `results:<search_id>`
(JSON, 24h TTL). Nothing else is ever written.

## Behavior knobs

| Env | Default | Meaning |
|---|---|---|
| `RATE_LIMIT` | 2 | lifetime searches per IP, no reset |
| `MAX_LINKS` | 25 | postings scraped per run |
| `MAX_MATCHES` | 8 | stop early once this many matches found |
| `PER_JOB_DELAY` | 3.0 | seconds between job evaluations (politeness) |

## Security notes

- **Keep the OpenCode key out of the repo.** The backend reads `OPENCODE_API_KEY`
  from the environment and never sends it to the frontend. An earlier standalone
  script had a key hardcoded; it has been removed, and that old key should be
  treated as leaked and rotated.
- CORS is an explicit origin whitelist; there is no wildcard anywhere.
- The rate limiter trusts the first `X-Forwarded-For` hop, which is correct behind
  Render's proxy.

## Repo layout

```
render.yaml      Render Blueprint (free-tier Docker web service definition)
backend/
  app/
    main.py       FastAPI app: kickoff, SSE stream, results, CORS, rate limiting
    pipeline.py   orchestration: plan → search ladder → scrape+eval loop → rank
    llm.py        OpenCode calls: query/rubric builder + per-job evaluator
    scraper.py    LinkedIn guest endpoints via httpx, headless Chromium fallback
    narrator.py   Harsh & Enzo copy, including the rate-limit messages
    store.py      Upstash Redis (or in-memory dev fallback): ratelimit + results
    config.py     env-driven settings
    models.py     recruiter form + job match schemas
  Dockerfile      Playwright base image (Chromium preinstalled) for Render
frontend/
  src/            React app: form → mission control (stage bar + ticker + live results)
```
