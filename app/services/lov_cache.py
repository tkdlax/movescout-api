from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from app.services import reference_cache as _ref_cache


async def get_or_load(
    user_id: UUID,
    loader: Callable[[], Awaitable[Any]],
    *,
    force_refresh: bool = False,
) -> Any:
    return await _ref_cache.get_or_load(
        user_id,
        "lov",
        loader,
        force_refresh=force_refresh,
    )


def clear_cache(user_id: UUID | None = None) -> None:
    _ref_cache.clear_cache(user_id, "lov")
