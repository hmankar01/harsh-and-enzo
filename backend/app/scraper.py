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

from .models import LocationSpec, SearchForm

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
    "?keywords={keywords}&f_TPR=r{seconds}&sortBy=DD&start={start}{extra}"
)
FULL_SEARCH_URL = (
    "https://www.linkedin.com/jobs/search/?keywords={keywords}&f_TPR=r{seconds}&sortBy=DD{extra}"
)

# LinkedIn's f_SB2 salary buckets: 1 => $40k+ ... 9 => $200k+
def _salary_bucket(floor: int) -> Optional[int]:
    if floor < 40000:
        return None
    return min(9, max(1, (floor - 20000) // 20000))


def _workplace_codes(loc: LocationSpec) -> str:
    """LinkedIn f_WT codes: 1=onsite, 2=remote, 3=hybrid. Empty string = any."""
    codes = []
    if loc.onsite:
        codes.append("1")
    if loc.remote:
        codes.append("2")
    if loc.hybrid:
        codes.append("3")
    if len(codes) in (0, 3):
        return ""  # none or all => no workplace-type filter
    return ",".join(codes)


def _location_variants(form: SearchForm) -> list[str]:
    """One 'extra' query-string per city (or one nationwide search when no cities
    are given), carrying workplace-type, radius, and salary filters."""
    loc = form.location
    wt = _workplace_codes(loc)
    salary = ""
    if form.salary_floor:
        bucket = _salary_bucket(form.salary_floor)
        if bucket:
            salary = f"&f_SB2={bucket}"

    variants = []
    for city in (loc.cities or [""]):
        extra = salary
        if city:
            extra += f"&location={urllib.parse.quote(city)}"
        if wt:
            extra += f"&f_WT={wt}"
        if loc.hybrid and loc.radius_miles:
            extra += f"&distance={loc.radius_miles}"
        variants.append(extra)
    return variants


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


AUTHWALL_MARKERS = (
    "sign in", "authwall", "verify you're a real person",
    "join linkedin", "let's do a quick verification",
)


def _is_authwall(text: str) -> bool:
    head = text[:500].lower()
    return any(m in head for m in AUTHWALL_MARKERS)


class Scraper:
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._browser_lock = asyncio.Lock()
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
            try:
                await self._browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass

    async def _page_content(self, url: str) -> str:
        """Render a page in headless Chromium and return its HTML."""
        if self._browser is None or not self._browser.is_connected():
            async with self._browser_lock:
                if self._browser is None or not self._browser.is_connected():
                    if self._browser is not None:
                        await self._browser.close()
                        self._browser = None
                    if self._playwright is None:
                        self._playwright = await async_playwright().start()
                    try:
                        self._browser = await self._playwright.chromium.launch(
                            headless=True, args=CHROMIUM_ARGS
                        )
                    except Exception:
                        self._browser = None
                        raise
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
        variants = _location_variants(form)

        # Fast path: guest API returns job-card HTML without needing a browser.
        # Paginate (25 cards/page) across each location and merge + dedupe.
        all_links: list[str] = []
        for extra in variants:
            for i, start in enumerate((0, 25, 50, 75)):
                if i:
                    await asyncio.sleep(0.5)  # polite gap between pages
                try:
                    response = await self._http.get(
                        GUEST_SEARCH_URL.format(
                            keywords=keywords, seconds=seconds, start=start, extra=extra
                        )
                    )
                    if response.status_code != 200:
                        break
                    page = _canonical_links(response.text)
                    if not page:
                        break
                    all_links.extend(page)
                    if len(page) < 25:
                        break
                except httpx.HTTPError:
                    break

        if all_links:
            seen: set[str] = set()
            return [l for l in all_links if not (l in seen or seen.add(l))]

        # Fallback: render the real search page headlessly.
        try:
            content = await self._page_content(
                FULL_SEARCH_URL.format(keywords=keywords, seconds=seconds, extra=variants[0])
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
                    if len(text) > 400 and "authwall" not in response.url.path and not _is_authwall(text):
                        return text
            except httpx.HTTPError:
                pass

        content = await self._page_content(url)
        text = _html_to_text(content)
        return "" if _is_authwall(text) else text

    @staticmethod
    async def polite_delay(base: float) -> None:
        await asyncio.sleep(base + random.uniform(0, 1.5))
