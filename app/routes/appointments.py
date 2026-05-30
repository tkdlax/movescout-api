from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.db import User
from app.models.schemas import CreateAppointmentRequest
from app.movescout.activities import (
    build_activity_date_filters,
    build_survey_activity_payload,
    create_or_update_activity,
    extract_activity_list,
    get_activities,
)
from app.movescout.pagination import fetch_all_activities_paginated
from app.movescout.client import MoveScoutError
from app.movescout.leads import extract_single_lead, get_lead_by_id, update_lead_from_appointment
from app.services.csv_export import generate_csv_content
from app.services.dedup import deduplicate_latest_per_lead
from app.services.movescout_service import with_movescout_client

router = APIRouter(tags=["appointments"])


@router.get("/leads/{lead_id}/appointments")
async def list_lead_appointments(
    request: Request,
    lead_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        response = await get_activities(client, lead_id=lead_id)
        items, total = extract_activity_list(response)
        return {"items": items, "total": total}

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/leads/{lead_id}/appointments", status_code=status.HTTP_201_CREATED)
async def create_lead_appointment(
    request: Request,
    lead_id: str,
    body: CreateAppointmentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    request.state.user_id = user.id

    async def callback(client: Any) -> dict[str, Any]:
        lead_response = await get_lead_by_id(client, lead_id)
        lead = extract_single_lead(lead_response)
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

        activity_payload = build_survey_activity_payload(
            lead,
            survey_date=body.survey_date,
            survey_duration_hours=body.survey_duration_hours,
            survey_type=body.survey_type,
            assignee_id=body.assignee_id,
        )
        activity_response = await create_or_update_activity(client, activity_payload)
        activity_result = activity_response.get("result", activity_response)

        updated_lead = dict(lead)
        updated_lead["dispositionId"] = 47
        await update_lead_from_appointment(client, updated_lead)

        activity_id = None
        if isinstance(activity_result, dict):
            activity_id = activity_result.get("id") or activity_result.get("activityId")

        return {"activityId": activity_id, "result": activity_result}

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/appointments")
async def list_appointments(
    request: Request,
    start_date: str | None = Query(default=None, alias="startDate"),
    end_date: str | None = Query(default=None, alias="endDate"),
    activity_type: int | None = Query(default=None, alias="type"),
    lead_id: str | None = Query(default=None, alias="leadId"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    request.state.user_id = user.id
    settings = get_settings()
    filters = build_activity_date_filters(start_date, end_date, activity_type, lead_id)

    async def callback(client: Any) -> dict[str, Any]:
        items, total = await fetch_all_activities_paginated(
            client,
            filters=filters,
            page_size=settings.export_page_size,
        )
        return {"items": items, "total": total}

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/appointments/latest-per-lead")
async def latest_appointment_per_lead(
    request: Request,
    start_date: str = Query(alias="startDate"),
    end_date: str = Query(alias="endDate"),
    format: str = Query(default="json"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    request.state.user_id = user.id
    settings = get_settings()
    filters = build_activity_date_filters(start_date, end_date, activity_type=1)

    async def callback(client: Any) -> Any:
        all_items, _total = await fetch_all_activities_paginated(
            client,
            filters=filters,
            page_size=settings.export_page_size,
        )
        deduped = deduplicate_latest_per_lead(all_items)

        if format == "csv":
            if not deduped:
                content = ""
            else:
                fieldnames = sorted({key for item in deduped for key in item.keys()})
                rows = [[str(item.get(f, "")) for f in fieldnames] for item in deduped]
                content = generate_csv_content(fieldnames, rows)
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            filename = f"appointments_latest_{timestamp}.csv"
            return StreamingResponse(
                iter([content]),
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        return {"items": deduped, "total": len(deduped)}

    try:
        return await with_movescout_client(db, user, callback)
    except MoveScoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
