from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_user
from app.config import get_settings
from app.database import get_db
from app.middleware.request import parse_filter_param
from app.models.db import User
from app.models.schemas import LeadListRequest, LeadQueryRequest
from app.movescout.client import MoveScoutError
from app.movescout.filters import build_filters, prepare_lead_filters
from app.movescout.leads import (
    build_get_all_lead_payload,
    create_or_update_lead,
    extract_single_lead,
    get_lead_by_id,
)
from app.movescout.pagination import (
    fetch_all_leads_paginated,
    leads_page_count_response,
    list_leads_page_response,
)
from app.movescout.responses import parse_abp_response
from app.services.csv_export import generate_csv_content, leads_to_csv_rows
from app.services.lead_merge import apply_lead_defaults, deep_merge
from app.services.movescout_service import with_movescout_client

router = APIRouter(prefix="/leads", tags=["leads"])


def _json_response(data: Any, *, status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=jsonable_encoder(data))


def _clamp_max_result_size(value: int, settings: Any) -> int:
    return min(value, settings.max_page_size)


@router.get("/page-count")
async def leads_page_count(
    request: Request,
    default_filter: int = Query(default=3, alias="defaultFilter", ge=0, le=12),
    max_result_size: int = Query(default=500, alias="maxResultSize", ge=1, le=1000),
    sort_field: str | None = Query(default=None, alias="sortField"),
    sort_dir: str = Query(default="desc", alias="sortDir"),
    filter_param: str | None = Query(default=None, alias="filter"),
    debug_upstream: bool = Query(default=False, alias="debugUpstream"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Probe MoveScout (maxResultCount=1) and return totalCount + pageCount for the query."""
    request.state.user_id = user.id
    settings = get_settings()
    batch = _clamp_max_result_size(max_result_size, settings)

    raw_filters = parse_filter_param(filter_param)
    try:
        filters = prepare_lead_filters(raw_filters) if raw_filters else []
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    async def callback(client: Any) -> dict[str, Any]:
        response = await leads_page_count_response(
            client,
            default_filter=default_filter,
            filters=filters,
            max_result_size=batch,
            sort_field=sort_field,
            sort_dir=sort_dir,
        )
        if debug_upstream:
            response = dict(response)
            response["upstreamPayload"] = build_get_all_lead_payload(
                default_filter=default_filter,
                filters=filters,
                page=1,
                page_size=batch,
                sort_field=sort_field,
                sort_dir=sort_dir,
            )
        return response

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("")
async def list_leads(
    request: Request,
    page: int = Query(default=1, ge=1),
    default_filter: int = Query(default=3, alias="defaultFilter", ge=0, le=12),
    max_result_size: int = Query(default=500, alias="maxResultSize", ge=1, le=1000),
    sort_field: str | None = Query(default=None, alias="sortField"),
    sort_dir: str = Query(default="desc", alias="sortDir"),
    filter_param: str | None = Query(default=None, alias="filter"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return one page of leads. Call GET /leads/page-count first to know how many pages exist."""
    request.state.user_id = user.id
    settings = get_settings()
    batch = _clamp_max_result_size(max_result_size, settings)

    raw_filters = parse_filter_param(filter_param)
    try:
        filters = prepare_lead_filters(raw_filters) if raw_filters else []
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    async def callback(client: Any) -> dict[str, Any]:
        return await list_leads_page_response(
            client,
            default_filter=default_filter,
            filters=filters,
            page=page,
            max_result_size=batch,
            sort_field=sort_field,
            sort_dir=sort_dir,
        )

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/export")
async def export_leads(
    request: Request,
    default_filter: int = Query(default=3, alias="defaultFilter", ge=0, le=12),
    sort_field: str | None = Query(default=None, alias="sortField"),
    sort_dir: str = Query(default="desc", alias="sortDir"),
    filter_param: str | None = Query(default=None, alias="filter"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    request.state.user_id = user.id
    settings = get_settings()

    raw_filters = parse_filter_param(filter_param)
    try:
        filters = prepare_lead_filters(raw_filters) if raw_filters else []
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    async def callback(client: Any) -> StreamingResponse:
        leads, _total = await fetch_all_leads_paginated(
            client,
            default_filter=default_filter,
            filters=filters,
            page_size=settings.export_page_size,
            sort_field=sort_field,
            sort_dir=sort_dir,
        )
        fieldnames, rows = leads_to_csv_rows(leads)
        content = generate_csv_content(fieldnames, rows)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"leads_{timestamp}.csv"
        return StreamingResponse(
            iter([content]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/query/page-count")
async def query_leads_page_count(
    request: Request,
    body: LeadListRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    request.state.user_id = user.id
    settings = get_settings()
    batch = _clamp_max_result_size(body.max_result_size, settings)

    try:
        filters = build_filters([f.model_dump() for f in body.filters], body.logic)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    async def callback(client: Any) -> dict[str, Any]:
        return await leads_page_count_response(
            client,
            default_filter=body.default_filter,
            filters=filters,
            max_result_size=batch,
            sort_field=body.sort_field,
            sort_dir=body.sort_dir,
        )

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/query")
async def query_leads(
    request: Request,
    body: LeadQueryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    request.state.user_id = user.id
    settings = get_settings()
    batch = _clamp_max_result_size(body.max_result_size, settings)

    try:
        filters = build_filters([f.model_dump() for f in body.filters], body.logic)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if body.export:
        async def export_callback(client: Any) -> StreamingResponse:
            leads, _total = await fetch_all_leads_paginated(
                client,
                default_filter=body.default_filter,
                filters=filters,
                page_size=settings.export_page_size,
                sort_field=body.sort_field,
                sort_dir=body.sort_dir,
            )
            fieldnames, rows = leads_to_csv_rows(leads)
            content = generate_csv_content(fieldnames, rows)
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            filename = f"leads_query_{timestamp}.csv"
            return StreamingResponse(
                iter([content]),
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        try:
            return await with_movescout_client(db, user, export_callback)
        except MoveScoutError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    async def callback(client: Any) -> dict[str, Any]:
        return await list_leads_page_response(
            client,
            default_filter=body.default_filter,
            filters=filters,
            page=body.page,
            max_result_size=batch,
            sort_field=body.sort_field,
            sort_dir=body.sort_dir,
        )

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/{lead_id}")
async def get_lead(
    request: Request,
    lead_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        response = await get_lead_by_id(client, lead_id)
        return parse_abp_response(response, action="get lead")

    try:
        result = await with_movescout_client(db, user, callback)
        return _json_response(result)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_lead(
    request: Request,
    body: dict[str, Any],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    request.state.user_id = user.id
    payload = apply_lead_defaults(body)

    async def callback(client: Any) -> dict[str, Any]:
        response = await create_or_update_lead(client, payload)
        return parse_abp_response(response, action="create lead")

    try:
        result = await with_movescout_client(db, user, callback)
        return _json_response(result, status_code=status.HTTP_201_CREATED)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.put("/{lead_id}")
async def update_lead(
    request: Request,
    lead_id: str,
    body: dict[str, Any],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        current_response = await get_lead_by_id(client, lead_id)
        current = extract_single_lead(current_response)
        if not current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        merged = deep_merge(current, body)
        merged["id"] = current.get("id") or lead_id
        response = await create_or_update_lead(client, merged)
        return parse_abp_response(response, action="update lead")

    try:
        result = await with_movescout_client(db, user, callback)
        return _json_response(result)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
