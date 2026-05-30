import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from app.config import get_settings

_lock = asyncio.Lock()
_cache: dict[str, tuple[Any, float]] = {}


def _cache_key(user_id: UUID, namespace: str) -> str:
    return f"{user_id}:{namespace}"


async def get_or_load(
    user_id: UUID,
    namespace: str,
    loader: Callable[[], Awaitable[Any]],
    *,
    force_refresh: bool = False,
) -> Any:
    key = _cache_key(user_id, namespace)
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


def clear_cache(user_id: UUID | None = None, namespace: str | None = None) -> None:
    if user_id is None and namespace is None:
        _cache.clear()
        return

    if user_id is not None and namespace is not None:
        _cache.pop(_cache_key(user_id, namespace), None)
        return

    prefix = f"{user_id}:" if user_id else None
    suffix = f":{namespace}" if namespace else None
    keys_to_remove = [
        k
        for k in _cache
        if (prefix is None or k.startswith(prefix)) and (suffix is None or k.endswith(suffix))
    ]
    for k in keys_to_remove:
        _cache.pop(k, None)
