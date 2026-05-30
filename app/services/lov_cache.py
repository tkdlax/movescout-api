import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from app.config import get_settings

_lock = asyncio.Lock()
_cache: dict[str, tuple[Any, float]] = {}


async def get_or_load(
    user_id: UUID,
    loader: Callable[[], Awaitable[Any]],
    *,
    force_refresh: bool = False,
) -> Any:
    key = str(user_id)
    ttl = get_settings().lov_cache_ttl_seconds
    now = time.monotonic()

    if not force_refresh:
        async with _lock:
            entry = _cache.get(key)
            if entry is not None and now - entry[1] < ttl:
                return entry[0]

    data = await loader()

    async with _lock:
        _cache[key] = (data, time.monotonic())

    return data


def clear_cache(user_id: UUID | None = None) -> None:
    if user_id is None:
        _cache.clear()
    else:
        _cache.pop(str(user_id), None)
