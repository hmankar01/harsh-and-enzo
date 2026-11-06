"""LinkedIn guest scraping.

Strategy per fetch: try the lightweight guest HTML endpoints over httpx first
(no browser, fast), fall back to headless Chromium via Playwright when LinkedIn
serves an authwall or an empty shell. headless=True always — deploy targets
have no display.
"""

import asyncio
import html as html_lib
import random
import re
import urllib.parse
from typing import Optional

import httpx
from playwright.async_api import async_playwright

from .models import SearchForm

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

JOB_ID_RE = re.compile(r"linkedin\.com/jobs/view/(?:[^\"'\s?]*?-)?(\d{6,})")
TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_RE = re.compile(r"<(script|style|noscript)\b.*?</\1>", re.DOTALL | re.IGNORECASE)

# Chromium flags tuned for small containers (Render's free tier is 512 MB RAM).
# --no-sandbox and --disable-dev-shm-usage avoid the two most common crash modes
# in a restricted container; --single-process trades some stability for much lower
# memory; --disable-gpu drops an unused subsystem.
CHROMIUM_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--single-process",
    "--disable-extensions",
    "--mute-audio",
]

GUEST_SEARCH_URL = (
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    "?keywords={keywords}&f_TPR=r{seconds}&sortBy=DD&start=0{extra}"
)
FULL_SEARCH_URL = (
    "https://www.linkedin.com/jobs/search/?keywords={keywords}&f_TPR=r{seconds}&sortBy=DD{extra}"
)

# LinkedIn's f_SB2 salary buckets: 1 => $40k+ ... 9 => $200k+
def _salary_bucket(floor: int) -> Optional[int]:
    if floor < 40000:
        return None
    return min(9, max(1, (floor - 20000) // 20000))


def _location_params(form: SearchForm) -> str:
    extra = ""
    loc = form.location
    if loc.mode == "remote":
        extra += "&f_WT=2"
    elif loc.city:
        extra += f"&location={urllib.parse.quote(loc.city)}"
        if loc.mode == "hybrid":
            extra += "&f_WT=3"
            if loc.radius_miles:
                extra += f"&distance={loc.radius_miles}"
    if form.salary_floor:
        bucket = _salary_bucket(form.salary_floor)
        if bucket:
            extra += f"&f_SB2={bucket}"
    return extra


def _html_to_text(raw: str) -> str:
    raw = SCRIPT_RE.sub(" ", raw)
    text = TAG_RE.sub(" ", raw)
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _canonical_links(raw: str) -> list[str]:
    seen: set[str] = set()
    links: list[str] = []
    for job_id in JOB_ID_RE.findall(raw):
        if job_id not in seen:
            seen.add(job_id)
            links.append(f"https://www.linkedin.com/jobs/view/{job_id}/")
    return links


class Scraper:
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._http = httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
            follow_redirects=True,
            timeout=25.0,
        )

    async def __aenter__(self) -> "Scraper":
        return self

    async def __aexit__(self, *exc) -> None:
        await self._http.aclose()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def _page_content(self, url: str) -> str:
        """Render a page in headless Chromium and return its HTML."""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True, args=CHROMIUM_ARGS
            )
        context = await self._browser.new_context(user_agent=USER_AGENT)
        try:
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2500)
            return await page.content()
        finally:
            await context.close()

    async def search_links(self, query: str, seconds: int, form: SearchForm) -> list[str]:
        """Return canonical job-view URLs for a boolean query within a time window."""
        keywords = urllib.parse.quote(query)
        extra = _location_params(form)

        # Fast path: guest API returns job-card HTML without needing a browser.
        try:
            response = await self._http.get(
                GUEST_SEARCH_URL.format(keywords=keywords, seconds=seconds, extra=extra)
            )
            if response.status_code == 200:
                links = _canonical_links(response.text)
                if links:
                    return links
        except httpx.HTTPError:
            pass

        # Fallback: render the real search page headlessly.
        try:
            content = await self._page_content(
                FULL_SEARCH_URL.format(keywords=keywords, seconds=seconds, extra=extra)
            )
            return _canonical_links(content)
        except Exception:
            return []

    async def job_text(self, url: str) -> str:
        """Return the readable text of a job posting page."""
        job_id_match = JOB_ID_RE.search(url)

        # Fast path: guest posting endpoint serves the description HTML directly.
        if job_id_match:
            guest_url = (
                "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/"
                f"{job_id_match.group(1)}"
            )
            try:
                response = await self._http.get(guest_url)
                if response.status_code == 200:
                    text = _html_to_text(response.text)
                    if len(text) > 400 and "authwall" not in response.url.path:
                        return text
            except httpx.HTTPError:
                pass

        content = await self._page_content(url)
        return _html_to_text(content)

    @staticmethod
    async def polite_delay(base: float) -> None:
        await asyncio.sleep(base + random.uniform(0, 1.5))
