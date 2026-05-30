from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_user
from app.config import get_settings
from app.database import get_db
from app.middleware.request import parse_filter_param
from app.models.db import User
from app.models.schemas import LeadQueryRequest
from app.movescout.client import MoveScoutError
from app.movescout.filters import build_filters
from app.movescout.leads import (
    create_or_update_lead,
    extract_lead_list,
    extract_single_lead,
    get_all_leads,
    get_lead_by_id,
)
from app.movescout.pagination import fetch_all_leads_paginated
from app.services.csv_export import generate_csv_content, leads_to_csv_rows
from app.services.lead_merge import apply_lead_defaults, deep_merge
from app.services.movescout_service import with_movescout_client

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("")
async def list_leads(
    request: Request,
    default_filter: int = Query(default=3, alias="defaultFilter", ge=0, le=12),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, alias="pageSize", ge=1, le=1000),
    sort_field: str | None = Query(default=None, alias="sortField"),
    sort_dir: str = Query(default="desc", alias="sortDir"),
    filter_param: str | None = Query(default=None, alias="filter"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    request.state.user_id = user.id
    settings = get_settings()
    page_size = min(page_size, settings.max_page_size)

    raw_filters = parse_filter_param(filter_param)
    try:
        filters = build_filters(raw_filters) if raw_filters else []
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    async def callback(client: Any) -> dict[str, Any]:
        response = await get_all_leads(
            client,
            default_filter=default_filter,
            filters=filters,
            page=page,
            page_size=page_size,
            sort_field=sort_field,
            sort_dir=sort_dir,
        )
        items, total = extract_lead_list(response)
        return {"items": items, "total": total, "page": page, "pageSize": page_size}

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
        filters = build_filters(raw_filters) if raw_filters else []
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    async def callback(client: Any) -> StreamingResponse:
        leads = await fetch_all_leads_paginated(
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
        return extract_single_lead(response)

    try:
        return await with_movescout_client(db, user, callback)
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
        return response.get("result", response) if isinstance(response, dict) else response

    try:
        return await with_movescout_client(db, user, callback)
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
        return response.get("result", response) if isinstance(response, dict) else response

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

    try:
        filters = build_filters([f.model_dump() for f in body.filters], body.logic)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if body.export:
        async def export_callback(client: Any) -> StreamingResponse:
            leads = await fetch_all_leads_paginated(
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
        response = await get_all_leads(
            client,
            default_filter=body.default_filter,
            filters=filters,
            page=body.page,
            page_size=body.page_size,
            sort_field=body.sort_field,
            sort_dir=body.sort_dir,
        )
        items, total = extract_lead_list(response)
        return {"items": items, "total": total, "page": body.page, "pageSize": body.page_size}

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
