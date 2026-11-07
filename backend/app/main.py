"""FastAPI app: rate-limited search kickoff, SSE progress stream, cached results.

POST /api/search               -> starts a pipeline run (429 with personality when over limit)
POST /api/search/{id}/cancel   -> cancels a running pipeline
GET  /api/search/{id}/stream   -> SSE: stage / log / match / done / error events
GET  /api/search/{id}/results  -> ranked matches from Redis (24h TTL)
GET  /api/health
"""

import asyncio
import json
import random
import time
import uuid
from dataclasses import dataclass, field

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from . import narrator
from .config import settings
from .models import SearchForm
from .pipeline import run_pipeline
from .store import check_rate_limit, load_results, refund_rate_limit

app = FastAPI(title="Harsh & Enzo Job Matcher")

# Explicit origin whitelist — no wildcard. Last-Event-ID enables SSE resume.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Last-Event-ID"],
)


@dataclass
class SearchRun:
    """In-memory event log for one pipeline run (single-instance demo scale).
    Consumers stream it with a cursor, so reconnects replay cleanly."""

    history: list[tuple[str, dict]] = field(default_factory=list)
    finished: bool = False
    cancelled: bool = False
    started_at: float = field(default_factory=time.time)


RUNS: dict[str, SearchRun] = {}
TERMINAL_EVENTS = {"done", "error"}
TASKS: set[asyncio.Task] = set()


def _client_ip(request: Request) -> str:
    # Render prepends the real client IP to X-Forwarded-For, so the first hop is
    # the client.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _prune_runs() -> None:
    # Drop stale runs (finished or not) so cancelled/crashed runs can't leak.
    cutoff = time.time() - 3600
    for key in [k for k, run in RUNS.items() if run.started_at < cutoff]:
        del RUNS[key]


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/search")
async def start_search(form: SearchForm, request: Request):
    _prune_runs()
    ip = _client_ip(request)
    allowed, remaining = await check_rate_limit(ip)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limited",
                "message": random.choice(narrator.LIMIT_MESSAGES).format(limit=settings.RATE_LIMIT),
                "contact_linkedin": settings.CONTACT_LINKEDIN,
                "contact_email": settings.CONTACT_EMAIL,
            },
        )

    search_id = uuid.uuid4().hex
    run = SearchRun()
    RUNS[search_id] = run

    async def emit(event: str, data: dict) -> None:
        run.history.append((event, data))
        if event in TERMINAL_EVENTS:
            run.finished = True

    def _on_done(_: asyncio.Task) -> None:
        # Refund the quota if the run failed before producing results.
        if run.history and run.history[-1][0] == "error":
            asyncio.create_task(refund_rate_limit(ip))

    task = asyncio.create_task(
        run_pipeline(search_id, form, emit, is_cancelled=lambda: run.cancelled)
    )
    TASKS.add(task)
    task.add_done_callback(TASKS.discard)
    task.add_done_callback(_on_done)
    return {"search_id": search_id, "searches_remaining": remaining}


@app.post("/api/search/{search_id}/cancel")
async def cancel_search(search_id: str):
    run = RUNS.get(search_id)
    if run is None:
        return JSONResponse(status_code=404, content={"error": "unknown_search"})
    run.cancelled = True
    return {"status": "cancelled"}


def _sse(event: str, data: dict, event_id: int) -> str:
    return f"id: {event_id}\nevent: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/api/search/{search_id}/stream")
async def stream_search(search_id: str, request: Request):
    run = RUNS.get(search_id)
    if run is None:
        return JSONResponse(status_code=404, content={"error": "unknown_search"})

    # Resume from Last-Event-ID on reconnect (EventSource sends it automatically).
    last_id = request.headers.get("last-event-id")
    if last_id is None or last_id == "":
        cursor = 0
    else:
        try:
            cursor = int(last_id) + 1
        except ValueError:
            cursor = 0

    async def event_source():
        nonlocal cursor
        idle = 0.0
        while True:
            if cursor < len(run.history):
                event, data = run.history[cursor]
                cursor += 1
                idle = 0.0
                yield _sse(event, data, cursor - 1)
                if event in TERMINAL_EVENTS:
                    return
                continue
            if run.finished:
                return
            await asyncio.sleep(0.4)
            idle += 0.4
            if idle >= 15.0:
                idle = 0.0
                yield ": heartbeat\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/search/{search_id}/results")
async def get_results(search_id: str):
    results = await load_results(search_id)
    if results is None:
        return JSONResponse(status_code=404, content={"error": "expired_or_unknown"})
    return results
