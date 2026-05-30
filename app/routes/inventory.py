from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_user
from app.database import get_db
from app.models.db import User
from app.movescout.alliance import get_alliance_by_lead_estimate_id
from app.movescout.client import MoveScoutError
from app.movescout.estimates import (
    get_brand_tariff_mapped_list,
    get_estimate_accessorial_details,
    get_estimate_auto_spot_details,
    get_estimate_customer_facing_notes,
    get_estimate_pricing_total,
    get_primary_estimate,
    get_segments_for_lead_estimate,
)
from app.movescout.inventory import (
    extract_estimate_list,
    get_all_estimates,
    get_all_rooms_by_delta_for_estimate,
    get_booker_id_of_estimate,
    get_estimate_for_inventory_tab,
    get_estimate_summary,
)
from app.movescout.responses import parse_abp_response
from app.services.inventory_service import fetch_inventory_by_lead, fetch_pricing_by_lead
from app.services.movescout_service import with_movescout_client

router = APIRouter(tags=["inventory"])


@router.get("/leads/{lead_id}/inventory")
async def get_lead_inventory(
    request: Request,
    lead_id: str,
    estimate_id: str | None = Query(default=None, alias="estimateId"),
    include_summary: bool = Query(default=True, alias="includeSummary"),
    shipping_only: bool = Query(default=False, alias="shippingOnly"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Resolve primary estimate (or use estimateId) and return room-grouped inventory."""
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        return await fetch_inventory_by_lead(
            client,
            lead_id,
            estimate_id=estimate_id,
            include_summary=include_summary,
            shipping_only=shipping_only,
        )

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/leads/{lead_id}/pricing")
async def get_lead_pricing(
    request: Request,
    lead_id: str,
    estimate_id: str | None = Query(default=None, alias="estimateId"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Resolve primary estimate (or estimateId) and return pricing totals JSON."""
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        return await fetch_pricing_by_lead(client, lead_id, estimate_id=estimate_id)

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/leads/{lead_id}/estimates/primary")
async def get_primary_estimate_for_lead(
    request: Request,
    lead_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        response = await get_primary_estimate(client, lead_id)
        return parse_abp_response(response, action="get primary estimate")

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/leads/{lead_id}/estimates")
async def list_estimates_for_lead(
    request: Request,
    lead_id: str,
    page: int = Query(default=1, ge=1),
    max_result_size: int = Query(default=15, alias="maxResultSize", ge=1, le=1000),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        response = await get_all_estimates(
            client,
            lead_id,
            page=page,
            page_size=max_result_size,
        )
        items, total = extract_estimate_list(response)
        return {"items": items, "totalCount": total, "page": page, "maxResultSize": max_result_size}

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/leads/{lead_id}/estimates/{estimate_id}")
async def get_estimate_detail(
    request: Request,
    lead_id: str,
    estimate_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        response = await get_estimate_for_inventory_tab(client, estimate_id)
        result = parse_abp_response(response, action="get estimate for inventory tab")
        if isinstance(result, dict) and result.get("leadId") is None:
            result["leadId"] = lead_id
        return result

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/leads/{lead_id}/estimates/{estimate_id}/summary")
async def get_estimate_summary_route(
    request: Request,
    lead_id: str,
    estimate_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        response = await get_estimate_summary(client, estimate_id)
        return parse_abp_response(response, action="get estimate summary")

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/leads/{lead_id}/estimates/{estimate_id}/rooms")
async def get_estimate_rooms(
    request: Request,
    lead_id: str,
    estimate_id: str,
    date: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    request.state.user_id = user.id

    async def callback(client: Any) -> Any:
        response = await get_all_rooms_by_delta_for_estimate(
            client,
            lead_id=lead_id,
            estimate_id=estimate_id,
            date=date,
        )
        return parse_abp_response(response, action="get rooms for estimate")

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/leads/{lead_id}/estimates/{estimate_id}/segments")
async def get_estimate_segments(
    request: Request,
    lead_id: str,
    estimate_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    request.state.user_id = user.id

    async def callback(client: Any) -> Any:
        response = await get_segments_for_lead_estimate(client, estimate_id)
        return parse_abp_response(response, action="get estimate segments")

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/leads/{lead_id}/estimates/{estimate_id}/accessorials")
async def get_estimate_accessorials(
    request: Request,
    lead_id: str,
    estimate_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    request.state.user_id = user.id

    async def callback(client: Any) -> Any:
        response = await get_estimate_accessorial_details(client, estimate_id)
        return parse_abp_response(response, action="get estimate accessorials")

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/leads/{lead_id}/estimates/{estimate_id}/pricing")
async def get_estimate_pricing(
    request: Request,
    lead_id: str,
    estimate_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    request.state.user_id = user.id

    async def callback(client: Any) -> Any:
        response = await get_estimate_pricing_total(client, estimate_id)
        return parse_abp_response(response, action="get estimate pricing")

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/leads/{lead_id}/estimates/{estimate_id}/tariffs")
async def get_estimate_tariffs(
    request: Request,
    lead_id: str,
    estimate_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    request.state.user_id = user.id

    async def callback(client: Any) -> Any:
        response = await get_brand_tariff_mapped_list(client, estimate_id)
        return parse_abp_response(response, action="get estimate tariffs")

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/leads/{lead_id}/estimates/{estimate_id}/auto-spot")
async def get_estimate_auto_spot(
    request: Request,
    lead_id: str,
    estimate_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    request.state.user_id = user.id

    async def callback(client: Any) -> Any:
        response = await get_estimate_auto_spot_details(client, estimate_id)
        return parse_abp_response(response, action="get estimate auto spot")

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/leads/{lead_id}/estimates/{estimate_id}/notes")
async def get_estimate_notes(
    request: Request,
    lead_id: str,
    estimate_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    request.state.user_id = user.id

    async def callback(client: Any) -> Any:
        response = await get_estimate_customer_facing_notes(client, estimate_id)
        return parse_abp_response(response, action="get estimate notes")

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/leads/{lead_id}/estimates/{estimate_id}/alliance")
async def get_estimate_alliance(
    request: Request,
    lead_id: str,
    estimate_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    request.state.user_id = user.id

    async def callback(client: Any) -> Any:
        response = await get_alliance_by_lead_estimate_id(client, estimate_id)
        return parse_abp_response(response, action="get alliance by estimate")

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/leads/{lead_id}/estimates/{estimate_id}/booker-id")
async def get_estimate_booker_id(
    request: Request,
    lead_id: str,
    estimate_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        response = await get_booker_id_of_estimate(client, estimate_id)
        booker_id = parse_abp_response(response, action="get booker id")
        return {"estimateId": estimate_id, "bookerId": booker_id}

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
