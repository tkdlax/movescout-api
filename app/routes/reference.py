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
    get_agent_list,
    get_all_make_model_details,
    get_all_transit_guide_season_configuration,
    get_custom_tariff_list,
    get_lead_source_programs,
    get_move_coordinator_list,
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
CACHE_AGENTS = "agents"


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


@router.get("/agents")
async def reference_agents(
    request: Request,
    refresh: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """All Sirva network agents (origin/destination/booker dropdowns)."""
    return await _cached_reference(
        request, user, db, CACHE_AGENTS, get_agent_list, refresh=refresh
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


@router.get("/move-coordinators")
async def reference_move_coordinators(
    request: Request,
    agency_id: int = Query(alias="agencyId"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Move coordinators for an agency — not cached (agency-specific)."""
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        response = await get_move_coordinator_list(client, agency_id)
        result = parse_abp_response(response, action="get move coordinators")
        return _normalize_list_result(result)

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/custom-tariffs")
async def reference_custom_tariffs(
    request: Request,
    brand_id: int = Query(alias="brandId"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Custom tariff list for a brand — not cached (brand-specific)."""
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        response = await get_custom_tariff_list(client, brand_id)
        result = parse_abp_response(response, action="get custom tariffs")
        return _normalize_list_result(result)

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/lead-source-programs")
async def reference_lead_source_programs(
    request: Request,
    agency_id: int = Query(alias="agencyId"),
    page: int = Query(default=1, ge=1),
    max_result_size: int = Query(default=100, alias="maxResultSize", ge=1, le=1000),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Lead source programs for an agency — not cached (agency-specific, paginated)."""
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        response = await get_lead_source_programs(
            client, agency_id, page=page, page_size=max_result_size
        )
        result = parse_abp_response(response, action="get lead source programs")
        return _normalize_list_result(result)

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
