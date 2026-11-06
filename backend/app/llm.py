"""LLM calls through the OpenCode gateway (OpenAI-compatible).

Model routing:
  QUERY_MODEL (fast/cheap) — one templated call turns the recruiter form into the
      LinkedIn boolean query, a 2-rung relaxation ladder, and the eval rubric.
  EVAL_MODEL (accuracy-sensitive) — judges each scraped posting and must return
      strict JSON, so point this at the strongest model your gateway routes to.
"""

import json
import re
import uuid
from typing import Optional

from openai import AsyncOpenAI

from .config import settings
from .models import SearchForm

_client: Optional[AsyncOpenAI] = None

# OpenCode Go requires a stable session id on every request (routing + prompt caching).
SESSION_ID = uuid.uuid4().hex


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.OPENCODE_API_KEY:
            raise RuntimeError("OPENCODE_API_KEY is not set")
        _client = AsyncOpenAI(
            api_key=settings.OPENCODE_API_KEY,
            base_url=settings.OPENCODE_BASE_URL,
            default_headers={
                # OpenCode Go rejects requests without this session header.
                "x-opencode-session": f"ses_{SESSION_ID}",
                "User-Agent": "harsh-and-enzo/1.0",
            },
        )
    return _client


def _extract_json(text: str) -> dict:
    """Parse JSON out of a model response, tolerating code fences and prose."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


async def _json_chat(model: str, system: str, user: str, retries: int = 2) -> dict:
    last_error: Optional[Exception] = None
    for _ in range(retries + 1):
        response = await _get_client().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        try:
            return _extract_json(content)
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
    raise RuntimeError(f"Model {model} never returned valid JSON: {last_error}")


PLAN_SYSTEM = """You are a technical sourcing strategist. You convert a recruiter's structured \
criteria into (a) LinkedIn boolean keyword queries and (b) an evaluation rubric. \
Respond with a single JSON object and nothing else."""

PLAN_USER_TEMPLATE = """Recruiter criteria (JSON):
{form_json}

Produce a JSON object with exactly these keys:

1. "queries": an array of exactly 3 LinkedIn boolean keyword search strings, ordered strict to loose:
   - queries[0]: full precision. Quoted role/skill phrases OR'd together, AND'd with quoted domain phrases derived from the selected domains.
   - queries[1]: first relaxation — DROP the domain filter group entirely (domains are the least important filter), keep role/skill terms.
   - queries[2]: second relaxation — also drop experience-level qualifiers and any niche skill terms; keep only the 2-3 broadest role terms OR'd together.
   Rules: use double quotes around multi-word phrases, use OR/AND in caps, keep each query under 12 terms. Do NOT include location, salary, or posting-date terms (those are URL parameters, not keywords).

2. "eval_criteria": a rigorous evaluation rubric as plain text, written as numbered rules an evaluator must apply to a job posting. It must cover, based strictly on the criteria above:
   - the acceptable experience range in years, and that postings demanding clearly more experience must be rejected
   - rejection of any posting whose title or level matches the excluded seniority list
   - required skill alignment (at least a meaningful overlap with the listed skills)
   - domain alignment: the role should apply AI/automation to at least one of the selected domains; describe each selected domain in one sentence
   - if sponsorship is required: reject postings that explicitly refuse visa sponsorship or require citizenship/permanent residency without exception
   - location fit per the stated location preference
   - rejection if the posting contains any of the exclusion keywords in a disqualifying way
   - if a salary floor is set: reject postings whose stated maximum compensation is clearly below it (postings with no salary listed are NOT rejected for salary)

   Critical principle the rubric must state explicitly: rejection requires positive disqualifying
   evidence in the posting. A posting that simply does not mention experience, location details,
   salary, or sponsorship must NOT be rejected on those rules. The only affirmative requirement
   is domain/skill alignment, which must actually be present in the role description.

Return only the JSON object."""


async def build_search_plan(form: SearchForm) -> dict:
    """One templated call → boolean query + relaxation ladder + eval rubric."""
    plan = await _json_chat(
        settings.QUERY_MODEL,
        PLAN_SYSTEM,
        PLAN_USER_TEMPLATE.format(form_json=form.model_dump_json(indent=2)),
    )
    queries = [q for q in plan.get("queries", []) if isinstance(q, str) and q.strip()]
    criteria = plan.get("eval_criteria", "")
    if not queries or not criteria:
        raise RuntimeError("Search plan was missing queries or eval_criteria")
    return {"queries": queries[:3], "eval_criteria": criteria}


EVAL_SYSTEM = """You are Enzo, an exacting technical recruiter. You evaluate one job posting \
against a rubric and respond with a single JSON object and nothing else."""

EVAL_USER_TEMPLATE = """Rubric — apply every rule rigorously; when a rule forces rejection, reject:
{criteria}

Job posting content (extracted from the page, may contain navigation noise — focus on the posting itself):
---
{job_text}
---

Return exactly one JSON object with these keys:
- "title": job title
- "company": company name
- "salary_range": stated compensation range, or "Not listed"
- "experience_required": exact experience wording from the posting, or "Not stated"
- "posted_date": posted timing as shown (e.g. "3 days ago", "1 hour ago"), or "Unknown"
- "is_match": true or false
- "reason": one or two sentences: which rubric rules it satisfies, or exactly which rule forced rejection"""


async def evaluate_job(eval_criteria: str, job_text: str) -> dict:
    return await _json_chat(
        settings.EVAL_MODEL,
        EVAL_SYSTEM,
        EVAL_USER_TEMPLATE.format(criteria=eval_criteria, job_text=job_text[:14000]),
    )
