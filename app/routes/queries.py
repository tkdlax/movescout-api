from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.db import User
from app.movescout.client import MoveScoutError
from app.movescout.filters import build_date_range_filter, build_filters, build_kendo_filter
from app.movescout.pagination import fetch_all_leads_paginated, list_leads_page_response
from app.services.csv_export import generate_csv_content, leads_to_csv_rows
from app.services.movescout_service import with_movescout_client

router = APIRouter(prefix="/queries", tags=["queries"])

BOOKED_DISPOSITION_ID = 46
SURVEY_SCHEDULED_DISPOSITION_ID = 47


async def _run_named_query(
    request: Request,
    user: User,
    db: AsyncSession,
    *,
    default_filter: int,
    filters: list[dict[str, Any]],
    format: str,
    page: int = 1,
    max_result_size: int = 500,
    sort_field: str | None = None,
    sort_dir: str = "desc",
) -> Any:
    request.state.user_id = user.id
    settings = get_settings()

    if format == "csv":
        async def export_callback(client: Any) -> StreamingResponse:
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
            filename = f"query_{timestamp}.csv"
            return StreamingResponse(
                iter([content]),
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        try:
            return await with_movescout_client(db, user, export_callback)
        except MoveScoutError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    batch = min(max_result_size, settings.max_page_size)

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


@router.get("/booked-no-reg")
async def booked_no_reg(
    request: Request,
    sales_rep_name: str | None = Query(default=None, alias="salesRepName"),
    format: str = Query(default="json"),
    page: int = Query(default=1, ge=1),
    max_result_size: int = Query(default=500, alias="maxResultSize", ge=1, le=1000),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    raw_filters = [
        {"field": "dispositionId", "op": "eq", "value": BOOKED_DISPOSITION_ID},
        {"field": "registrationNumber", "op": "isnull", "value": None},
    ]
    if sales_rep_name:
        raw_filters.append({"field": "salesRepName", "op": "contains", "value": sales_rep_name})

    filters = build_filters(raw_filters)
    return await _run_named_query(
        request, user, db,
        default_filter=3,
        filters=filters,
        format=format,
        page=page,
        max_result_size=max_result_size,
    )


@router.get("/scheduled-surveys")
async def scheduled_surveys(
    request: Request,
    start: str = Query(),
    end: str = Query(),
    format: str = Query(default="json"),
    page: int = Query(default=1, ge=1),
    max_result_size: int = Query(default=500, alias="maxResultSize", ge=1, le=1000),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    filters = [
        build_kendo_filter("dispositionId", "eq", SURVEY_SCHEDULED_DISPOSITION_ID),
        build_date_range_filter("creationTime", start, end),
    ]
    return await _run_named_query(
        request, user, db,
        default_filter=3,
        filters=filters,
        format=format,
        page=page,
        max_result_size=max_result_size,
    )


@router.get("/unassigned")
async def unassigned_leads(
    request: Request,
    format: str = Query(default="json"),
    page: int = Query(default=1, ge=1),
    max_result_size: int = Query(default=500, alias="maxResultSize", ge=1, le=1000),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    filters = build_filters([
        {"field": "salesRepName", "op": "isnull", "value": None},
    ])
    return await _run_named_query(
        request, user, db,
        default_filter=3,
        filters=filters,
        format=format,
        page=page,
        max_result_size=max_result_size,
    )


@router.get("/my-leads")
async def my_leads(
    request: Request,
    format: str = Query(default="json"),
    page: int = Query(default=1, ge=1),
    max_result_size: int = Query(default=500, alias="maxResultSize", ge=1, le=1000),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    if not user.sales_rep_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User profile has no sales_rep_name configured",
        )

    filters = build_filters([
        {"field": "salesRepName", "op": "contains", "value": user.sales_rep_name},
    ])
    return await _run_named_query(
        request, user, db,
        default_filter=3,
        filters=filters,
        format=format,
        page=page,
        max_result_size=max_result_size,
    )
