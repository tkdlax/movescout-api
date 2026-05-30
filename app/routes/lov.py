from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_user
from app.database import get_db
from app.models.db import User
from app.movescout.client import MoveScoutError
from app.movescout.lov import get_all_list_of_values
from app.movescout.responses import parse_abp_response
from app.services.lov_cache import get_or_load
from app.services.movescout_service import with_movescout_client

router = APIRouter(tags=["lov"])


def _normalize_lov_result(result: Any) -> dict[str, Any]:
    if isinstance(result, list):
        return {"items": result, "count": len(result)}
    if isinstance(result, dict):
        items = result.get("items")
        if isinstance(items, list):
            return {
                **result,
                "count": result.get("count") or result.get("totalCount") or len(items),
            }
    return {"items": result, "count": 1 if result is not None else 0}


@router.get("/lov")
async def list_of_values(
    request: Request,
    refresh: bool = Query(default=False, description="Bypass cache and refetch from MoveScout"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Pass-through for MoveScout ListOfValue (enum/LOV definitions). Cached per API user."""
    request.state.user_id = user.id

    async def load(client: Any) -> dict[str, Any]:
        response = await get_all_list_of_values(client)
        result = parse_abp_response(response, action="get list of values")
        return _normalize_lov_result(result)

    async def callback(client: Any) -> dict[str, Any]:
        async def loader() -> dict[str, Any]:
            return await load(client)

        return await get_or_load(user.id, loader, force_refresh=refresh)

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
