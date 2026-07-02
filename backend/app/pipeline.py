"""The multi-minute pipeline: plan → search (with fallback ladder) → per-job
scrape + eval (streamed live) → rank → cache in Redis for 24h.

Emits events through an async callback; the SSE endpoint relays them."""

import re
from typing import Awaitable, Callable

from . import narrator
from .config import settings
from .llm import build_search_plan, evaluate_job
from .models import SearchForm
from .scraper import Scraper
from .store import save_results

Emit = Callable[[str, dict], Awaitable[None]]

TIME_FILTERS = [86400, 172800, 259200]  # 24h -> 48h -> 72h


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


async def _log(emit: Emit, agent: str, text: str, kind: str = "info") -> None:
    await emit("log", {"agent": agent, "text": text, "kind": kind})


async def _find_links(scraper: Scraper, queries: list[str], form: SearchForm, emit: Emit) -> list[str]:
    """Fallback ladder: query rung 0 walks the time windows; relaxed rungs use 72h."""
    for rung, query in enumerate(queries):
        if rung > 0:
            await _log(emit, "enzo", narrator.ENZO_RELAXING[min(rung - 1, 1)])
        windows = TIME_FILTERS if rung == 0 else [TIME_FILTERS[-1]]
        for seconds in windows:
            await _log(emit, "harsh", narrator.HARSH_SEARCHING[seconds])
            links = await scraper.search_links(query, seconds, form)
            if links:
                await _log(emit, "harsh", narrator.pick(narrator.HARSH_FOUND, n=len(links)))
                return links
            await scraper.polite_delay(2.0)
    return []


async def run_pipeline(search_id: str, form: SearchForm, emit: Emit) -> None:
    try:
        await emit("stage", {"stage": "searching"})
        await _log(emit, "harsh", narrator.pick(narrator.HARSH_WARMUP))
        await _log(emit, "enzo", narrator.pick(narrator.ENZO_PLANNING))

        plan = await build_search_plan(form)

        matches: list[dict] = []
        evaluated = 0

        async with Scraper() as scraper:
            links = await _find_links(scraper, plan["queries"], form, emit)

            if not links:
                await _log(
                    emit, "system",
                    "Even with the net wide open, LinkedIn came back empty. "
                    "Try broader skills or a looser location.",
                )
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
            for index, url in enumerate(targets, 1):
                if len(matches) >= settings.MAX_MATCHES:
                    await _log(
                        emit, "system",
                        f"That's {settings.MAX_MATCHES} solid matches — the duo calls it a wrap.",
                    )
                    break

                await _log(emit, "harsh", narrator.pick(narrator.HARSH_FETCHING, i=index, total=len(targets)))
                try:
                    text = await scraper.job_text(url)
                except Exception:
                    text = ""
                if len(text) < 300:
                    await _log(emit, "harsh", narrator.pick(narrator.HARSH_SCRAPE_FAIL), kind="reject")
                    continue

                await _log(emit, "enzo", narrator.pick(narrator.ENZO_READING, i=index))
                try:
                    verdict = await evaluate_job(plan["eval_criteria"], text)
                except Exception:
                    await _log(emit, "enzo", f"Enzo's notes on job #{index} caught fire. Skipping it.", kind="reject")
                    continue

                evaluated += 1
                verdict["url"] = url

                if verdict.get("is_match") is True:
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

                await scraper.polite_delay(settings.PER_JOB_DELAY)

        await emit("stage", {"stage": "ranking"})
        await _log(emit, "enzo", narrator.pick(narrator.RANKING))
        matches.sort(key=lambda j: parse_recency(j["posted_date"]))
        ranked = [{**job, "rank": i} for i, job in enumerate(matches, 1)]

        payload = {"matches": ranked, "evaluated": evaluated}
        await save_results(search_id, payload)

        await emit("stage", {"stage": "done"})
        await emit("done", {**payload, "no_results": len(ranked) == 0})

    except Exception as e:
        await emit("error", {"message": f"The mission hit a wall: {e}"})
