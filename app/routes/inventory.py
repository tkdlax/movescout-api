from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_user
from app.database import get_db
from app.models.db import User
from app.movescout.alliance import get_alliance_by_lead_estimate_id
from app.movescout.client import MoveScoutError
from app.movescout.estimates import (
    calculate_estimation_pricing,
    get_brand_tariff_mapped_list,
    get_estimate_accessorial_details,
    get_estimate_auto_spot_details,
    get_estimate_customer_facing_notes,
    get_estimate_pricing_total,
    get_estimate_tariff_by_effective_date,
    get_primary_estimate,
    get_segments_for_lead_estimate,
    update_lead_estimate,
)
from app.movescout.inventory import (
    extract_estimate_list,
    get_all_estimates,
    get_all_rooms_by_delta_for_estimate,
    get_booker_id_of_estimate,
    get_estimate_for_inventory_tab,
    get_estimate_summary,
)
from app.movescout.inventory_write import (
    create_article_from_inventory,
    create_or_update_article_for_inventory,
    create_or_update_article_for_list_inventory,
    create_or_update_estimates,
    create_or_update_room,
    get_all_articles_group_by_room,
    save_estimate_with_true_flag,
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


@router.get("/leads/{lead_id}/estimates/{estimate_id}/tariff-effective")
async def get_estimate_tariff_effective(
    request: Request,
    lead_id: str,
    estimate_id: str,
    tariff_id: int = Query(alias="tariffId"),
    tariff_name: str = Query(alias="tariffName"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get tariff details for an estimate based on effective date."""
    request.state.user_id = user.id

    async def callback(client: Any) -> Any:
        response = await get_estimate_tariff_by_effective_date(
            client,
            estimate_id=estimate_id,
            tariff_id=tariff_id,
            tariff_name=tariff_name,
        )
        return parse_abp_response(response, action="get tariff by effective date")

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/leads/{lead_id}/estimates/{estimate_id}/rooms/{room_id}/articles")
async def get_room_article_catalog(
    request: Request,
    lead_id: str,
    estimate_id: str,
    room_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get article catalog for a specific room (standard library articles)."""
    request.state.user_id = user.id

    async def callback(client: Any) -> Any:
        response = await get_all_articles_group_by_room(
            client,
            lead_id=lead_id,
            estimate_id=estimate_id,
            room_id=room_id,
        )
        return parse_abp_response(response, action="get articles by room")

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/leads/{lead_id}/estimates", status_code=status.HTTP_201_CREATED)
async def create_estimate(
    request: Request,
    lead_id: str,
    body: dict[str, Any],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create an estimate (with or without inventory)."""
    request.state.user_id = user.id
    body["leadId"] = int(lead_id) if lead_id.isdigit() else lead_id

    async def callback(client: Any) -> dict[str, Any]:
        response = await create_or_update_estimates(client, body)
        result = parse_abp_response(response, action="create estimate")
        return {"estimateId": result, "leadId": lead_id}

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.put("/leads/{lead_id}/estimates/{estimate_id}")
async def update_estimate(
    request: Request,
    lead_id: str,
    estimate_id: str,
    body: dict[str, Any],
    tab_switch_flag: bool = Query(default=False, alias="tabSwitchFlag"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update an existing lead estimate (tariff, pricing fields, etc.)."""
    request.state.user_id = user.id
    body["id"] = int(estimate_id) if estimate_id.isdigit() else estimate_id
    body["leadId"] = int(lead_id) if lead_id.isdigit() else lead_id

    async def callback(client: Any) -> dict[str, Any]:
        response = await update_lead_estimate(client, body, tab_switch_flag=tab_switch_flag)
        return parse_abp_response(response, action="update estimate")

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/leads/{lead_id}/estimates/{estimate_id}/rooms", status_code=status.HTTP_201_CREATED)
async def create_room(
    request: Request,
    lead_id: str,
    estimate_id: str,
    body: dict[str, Any],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create or update a room for an estimate."""
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        response = await create_or_update_room(client, body)
        result = parse_abp_response(response, action="create room")
        return {"roomId": result, "estimateId": estimate_id}

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/leads/{lead_id}/estimates/{estimate_id}/rooms/{room_id}/articles",
    status_code=status.HTTP_201_CREATED,
)
async def create_custom_article(
    request: Request,
    lead_id: str,
    estimate_id: str,
    room_id: int,
    body: dict[str, Any],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a custom article for a room."""
    request.state.user_id = user.id
    body["roomId"] = room_id

    async def callback(client: Any) -> dict[str, Any]:
        response = await create_article_from_inventory(client, body)
        result = parse_abp_response(response, action="create custom article")
        return {"articleId": result, "roomId": room_id}

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.put("/leads/{lead_id}/estimates/{estimate_id}/inventory/lines")
async def update_inventory_lines(
    request: Request,
    lead_id: str,
    estimate_id: str,
    body: list[dict[str, Any]],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update inventory line items (quantities, weights, etc.)."""
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        response = await create_or_update_article_for_list_inventory(client, body)
        result = parse_abp_response(response, action="update inventory lines")
        return {"result": result, "estimateId": estimate_id}

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/leads/{lead_id}/estimates/{estimate_id}/inventory/article")
async def update_inventory_article(
    request: Request,
    lead_id: str,
    estimate_id: str,
    body: dict[str, Any],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update a single inventory article in place (qty, weight, cube changes).

    This is distinct from the bulk /inventory/lines endpoint. Use this for
    in-place edits on existing articles (e.g., qty bump 2→3, weight/cube changes).

    Key fields from P3-F packet evidence:
    - estimatesId: Estimate ID
    - articleId: Article catalog ID (required)
    - shippingQty: New shipping quantity
    - weight: Article weight
    - cube: Article cube (may be string or int)
    - isQtyChange: Set to true when editing quantity
    - roomId, segmentId: Location identifiers

    Response is the full Calculate pricing result.
    """
    request.state.user_id = user.id
    body["estimatesId"] = int(estimate_id) if estimate_id.isdigit() else estimate_id

    async def callback(client: Any) -> dict[str, Any]:
        response = await create_or_update_article_for_inventory(client, body)
        return parse_abp_response(response, action="update inventory article")

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/leads/{lead_id}/estimates/{estimate_id}/inventory/save")
async def save_estimate_inventory(
    request: Request,
    lead_id: str,
    estimate_id: str,
    density: int = Query(default=7),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Commit/save inventory changes for an estimate."""
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        response = await save_estimate_with_true_flag(
            client,
            estimate_id=estimate_id,
            lead_id=lead_id,
            density=density,
        )
        result = parse_abp_response(response, action="save estimate inventory")
        return {"success": True, "result": result, "estimateId": estimate_id}

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/leads/{lead_id}/estimates/{estimate_id}/calculate-pricing")
async def calculate_pricing(
    request: Request,
    lead_id: str,
    estimate_id: str,
    body: dict[str, Any],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Calculate pricing for an estimate."""
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        response = await calculate_estimation_pricing(client, body)
        return parse_abp_response(response, action="calculate pricing")

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
