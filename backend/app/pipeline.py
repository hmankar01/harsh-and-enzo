"""The multi-minute pipeline: plan → search (with fallback ladder) → per-job
scrape + eval (streamed live) → rank → cache in Redis for 24h.

Emits events through an async callback; the SSE endpoint relays them."""

import asyncio
import re
from typing import Awaitable, Callable

from . import narrator
from .config import settings
from .llm import build_search_plan, evaluate_job
from .models import SearchForm
from .scraper import Scraper
from .store import save_results

Emit = Callable[[str, dict], Awaitable[None]]
IsCancelled = Callable[[], bool]

TIME_FILTERS = [86400, 172800, 259200]  # 24h -> 48h -> 72h

# Cap concurrent runs so a few visitors can't OOM the small (512 MB) instance
# with multiple Chromium browsers at once.
PIPELINE_SEMAPHORE = asyncio.Semaphore(2)

# How many jobs to scrape + evaluate concurrently within a single run.
EVAL_CONCURRENCY = 2


def parse_recency(posted: str) -> int:
    """Lower is fresher. Mirrors the original script's ranking."""
    text = (posted or "").lower()
    if "minute" in text or "hour" in text or "just now" in text:
        return 0
    if "day" in text:
        digits = [int(s) for s in re.findall(r"\d+", text)]
        return digits[0] if digits else 1
    if "week" in text:
        digits = [int(s) for s in re.findall(r"\d+", text)]
        return (digits[0] if digits else 1) * 7
    return 99


def _as_bool(value) -> bool:
    """Coerce an LLM-returned truthy value to a real boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in ("true", "yes", "1", "y")


async def _log(emit: Emit, agent: str, text: str, kind: str = "info") -> None:
    await emit("log", {"agent": agent, "text": text, "kind": kind})


async def _find_links(
    scraper: Scraper, queries: list[str], form: SearchForm, emit: Emit, is_cancelled: IsCancelled
) -> list[str]:
    """Fallback ladder: query rung 0 walks the time windows; relaxed rungs use 72h."""
    for rung, query in enumerate(queries):
        if is_cancelled():
            return []
        if rung > 0:
            await _log(emit, "enzo", narrator.ENZO_RELAXING[min(rung - 1, 1)])
        windows = TIME_FILTERS if rung == 0 else [TIME_FILTERS[-1]]
        for seconds in windows:
            if is_cancelled():
                return []
            await _log(emit, "harsh", narrator.HARSH_SEARCHING[seconds])
            links = await scraper.search_links(query, seconds, form)
            if links:
                await _log(emit, "harsh", narrator.pick(narrator.HARSH_FOUND, n=len(links)))
                return links
            await scraper.polite_delay(2.0)
    return []


async def _scrape_and_eval(scraper: Scraper, criteria: str, url: str) -> tuple[dict | None, str]:
    """Scrape + evaluate one job concurrently. Returns (verdict, status) where
    status is "ok", "scrape_fail", or "eval_fail"."""
    try:
        text = await scraper.job_text(url)
    except Exception:
        text = ""
    if len(text) < 300:
        return None, "scrape_fail"
    try:
        verdict = await evaluate_job(criteria, text)
    except Exception:
        return None, "eval_fail"
    if not isinstance(verdict, dict):
        return None, "eval_fail"
    return verdict, "ok"


async def run_pipeline(
    search_id: str, form: SearchForm, emit: Emit, is_cancelled: IsCancelled
) -> None:
    async with PIPELINE_SEMAPHORE:
        try:
            await emit("stage", {"stage": "searching"})
            await _log(emit, "harsh", narrator.pick(narrator.HARSH_WARMUP))
            await _log(emit, "enzo", narrator.pick(narrator.ENZO_PLANNING))

            plan = await build_search_plan(form)

            matches: list[dict] = []
            evaluated = 0

            async with Scraper() as scraper:
                links = await _find_links(scraper, plan["queries"], form, emit, is_cancelled)

                if is_cancelled():
                    return

                if not links:
                    await _log(
                        emit, "system",
                        "Even with the net wide open, LinkedIn came back empty. "
                        "Try broader skills or a looser location.",
                    )
                    await save_results(search_id, {"matches": [], "evaluated": 0})
                    await emit("stage", {"stage": "done"})
                    await emit("done", {"matches": [], "evaluated": 0, "no_results": True})
                    return

                await emit("stage", {"stage": "scraping"})
                targets = links[: settings.MAX_LINKS]
                await _log(
                    emit, "system",
                    f"Queue locked: {len(targets)} postings to investigate.",
                )

                await emit("stage", {"stage": "evaluating"})
                for batch_start in range(0, len(targets), EVAL_CONCURRENCY):
                    if is_cancelled():
                        return
                    if len(matches) >= settings.MAX_MATCHES:
                        await _log(
                            emit, "system",
                            f"That's {settings.MAX_MATCHES} solid matches — the duo calls it a wrap.",
                        )
                        break

                    batch = targets[batch_start : batch_start + EVAL_CONCURRENCY]

                    for offset in range(len(batch)):
                        await _log(
                            emit, "harsh",
                            narrator.pick(
                                narrator.HARSH_FETCHING,
                                i=batch_start + offset + 1,
                                total=len(targets),
                            ),
                        )

                    results = await asyncio.gather(
                        *(_scrape_and_eval(scraper, plan["eval_criteria"], url) for url in batch)
                    )

                    stop = False
                    for offset, (url, (verdict, status)) in enumerate(zip(batch, results)):
                        if is_cancelled():
                            return
                        if len(matches) >= settings.MAX_MATCHES:
                            await _log(
                                emit, "system",
                                f"That's {settings.MAX_MATCHES} solid matches — the duo calls it a wrap.",
                            )
                            stop = True
                            break

                        idx = batch_start + offset + 1
                        if status == "scrape_fail":
                            await _log(emit, "harsh", narrator.pick(narrator.HARSH_SCRAPE_FAIL), kind="reject")
                            continue
                        if status == "eval_fail":
                            await _log(emit, "enzo", f"Enzo's notes on job #{idx} caught fire. Skipping it.", kind="reject")
                            continue

                        await _log(emit, "enzo", narrator.pick(narrator.ENZO_READING, i=idx))
                        evaluated += 1
                        verdict["url"] = url

                        if _as_bool(verdict.get("is_match")):
                            job = {
                                "title": verdict.get("title") or "Unknown title",
                                "company": verdict.get("company") or "Unknown company",
                                "salary_range": verdict.get("salary_range") or "Not listed",
                                "experience_required": verdict.get("experience_required") or "Not stated",
                                "posted_date": verdict.get("posted_date") or "Unknown",
                                "url": url,
                                "reason": verdict.get("reason") or "",
                            }
                            matches.append(job)
                            await _log(
                                emit, "enzo",
                                narrator.pick(narrator.ENZO_MATCH, title=job["title"], company=job["company"]),
                                kind="match",
                            )
                            await emit("match", job)
                        else:
                            reason = (verdict.get("reason") or "didn't clear the rubric").rstrip(".")
                            await _log(
                                emit, "enzo",
                                narrator.pick(narrator.ENZO_REJECT, reason=reason + "."),
                                kind="reject",
                            )

                    if stop:
                        break

                    # One polite pause per batch (bounded concurrency stays gentle).
                    await scraper.polite_delay(settings.PER_JOB_DELAY)

            if is_cancelled():
                return

            await emit("stage", {"stage": "ranking"})
            await _log(emit, "enzo", narrator.pick(narrator.RANKING))
            matches.sort(key=lambda j: parse_recency(j["posted_date"]))
            ranked = [{**job, "rank": i} for i, job in enumerate(matches, 1)]

            payload = {"matches": ranked, "evaluated": evaluated}
            try:
                await save_results(search_id, payload)
            except Exception:
                pass  # a cache failure must never hide a completed run

            await emit("stage", {"stage": "done"})
            await emit("done", {**payload, "no_results": len(ranked) == 0})

        except Exception as e:
            await emit("error", {"message": f"The mission hit a wall: {e}"})
