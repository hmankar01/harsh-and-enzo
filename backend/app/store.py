"""State layer: Upstash Redis in production, in-memory fallback for local dev.

Only two kinds of keys exist, both with 24h TTLs:
  ratelimit:<ip>      -> integer counter
  results:<search_id> -> JSON blob of final ranked matches
Nothing persists beyond the TTL. There is no database.
"""

import asyncio
import json
import time
from typing import Optional

from .config import settings


class MemoryStore:
    """Dev-only stand-in for Redis with TTL semantics."""

    def __init__(self):
        self._data: dict[str, tuple[str, float]] = {}
        self._lock = asyncio.Lock()

    def _alive(self, key: str) -> Optional[str]:
        item = self._data.get(key)
        if item is None:
            return None
        value, expires = item
        if time.time() > expires:
            del self._data[key]
            return None
        return value

    async def incr_with_ttl(self, key: str, ttl: int) -> int:
        async with self._lock:
            current = self._alive(key)
            if current is None:
                self._data[key] = ("1", time.time() + ttl)
                return 1
            value = int(current) + 1
            _, expires = self._data[key]
            self._data[key] = (str(value), expires)
            return value

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self._data[key] = (value, time.time() + ttl)

    async def get(self, key: str) -> Optional[str]:
        return self._alive(key)

    async def ttl(self, key: str) -> int:
        item = self._data.get(key)
        if item is None:
            return -2
        return max(0, int(item[1] - time.time()))


class RedisStore:
    def __init__(self, url: str):
        import redis.asyncio as redis

        self._r = redis.from_url(url, decode_responses=True)

    async def incr_with_ttl(self, key: str, ttl: int) -> int:
        value = await self._r.incr(key)
        if value == 1:
            await self._r.expire(key, ttl)
        return value

    async def setex(self, key: str, ttl: int, value: str) -> None:
        await self._r.setex(key, ttl, value)

    async def get(self, key: str) -> Optional[str]:
        return await self._r.get(key)

    async def ttl(self, key: str) -> int:
        return await self._r.ttl(key)


store = RedisStore(settings.REDIS_URL) if settings.REDIS_URL else MemoryStore()


async def check_rate_limit(ip: str) -> tuple[bool, int, int]:
    """Increment the counter for this IP. Returns (allowed, remaining, retry_after_seconds)."""
    key = f"ratelimit:{ip}"
    count = await store.incr_with_ttl(key, settings.RATE_LIMIT_TTL)
    if count > settings.RATE_LIMIT:
        retry_after = await store.ttl(key)
        return False, 0, max(retry_after, 0)
    return True, settings.RATE_LIMIT - count, 0


async def save_results(search_id: str, payload: dict) -> None:
    await store.setex(f"results:{search_id}", settings.RESULT_TTL, json.dumps(payload))


async def load_results(search_id: str) -> Optional[dict]:
    raw = await store.get(f"results:{search_id}")
    return json.loads(raw) if raw else None
