from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_user
from app.database import get_db
from app.models.db import User
from app.movescout.alliance import (
    list_price_classes,
    list_service_item_categories,
    list_service_items,
    list_service_items_types,
)
from app.movescout.client import MoveScoutError
from app.movescout.reference_data import (
    get_all_make_model_details,
    get_all_transit_guide_season_configuration,
)
from app.movescout.responses import parse_abp_response
from app.services.movescout_service import with_movescout_client
from app.services.reference_cache import get_or_load

router = APIRouter(prefix="/reference", tags=["reference"])

CACHE_SERVICE_ITEMS = "service_items"
CACHE_SERVICE_ITEM_TYPES = "service_item_types"
CACHE_SERVICE_ITEM_CATEGORIES = "service_item_categories"
CACHE_VEHICLES = "vehicles"
CACHE_TRANSIT_SEASONS = "transit_seasons"


def _normalize_list_result(result: Any) -> dict[str, Any]:
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


async def _cached_reference(
    request: Request,
    user: User,
    db: AsyncSession,
    namespace: str,
    loader_fn: Any,
    *,
    refresh: bool = False,
) -> dict[str, Any]:
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        async def loader() -> dict[str, Any]:
            response = await loader_fn(client)
            result = parse_abp_response(response, action=f"load {namespace}")
            return _normalize_list_result(result)

        return await get_or_load(user.id, namespace, loader, force_refresh=refresh)

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/service-items")
async def reference_service_items(
    request: Request,
    refresh: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _cached_reference(
        request, user, db, CACHE_SERVICE_ITEMS, list_service_items, refresh=refresh
    )


@router.get("/service-item-types")
async def reference_service_item_types(
    request: Request,
    refresh: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _cached_reference(
        request, user, db, CACHE_SERVICE_ITEM_TYPES, list_service_items_types, refresh=refresh
    )


@router.get("/service-item-categories")
async def reference_service_item_categories(
    request: Request,
    refresh: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _cached_reference(
        request,
        user,
        db,
        CACHE_SERVICE_ITEM_CATEGORIES,
        list_service_item_categories,
        refresh=refresh,
    )


@router.get("/vehicles")
async def reference_vehicles(
    request: Request,
    refresh: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _cached_reference(
        request, user, db, CACHE_VEHICLES, get_all_make_model_details, refresh=refresh
    )


@router.get("/transit-seasons")
async def reference_transit_seasons(
    request: Request,
    refresh: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _cached_reference(
        request,
        user,
        db,
        CACHE_TRANSIT_SEASONS,
        get_all_transit_guide_season_configuration,
        refresh=refresh,
    )


@router.get("/price-classes")
async def reference_price_classes(
    request: Request,
    booker_id: str = Query(alias="bookerId"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Alliance price classes for a booker/agency — not cached (booker-specific)."""
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        response = await list_price_classes(client, booker_id)
        result = parse_abp_response(response, action="list price classes")
        return _normalize_list_result(result)

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
