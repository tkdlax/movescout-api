import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_user
from app.database import get_db
from app.models.db import User
from app.models.schemas import (
    SalesReportCreateRequest,
    SalesReportJobCreatedResponse,
    SalesReportJobStatusResponse,
)
from app.reports.lead_filters import validate_move_type
from app.reports.sales_params import normalize_sales_report_params
from app.services.report_callback import validate_callback_url
from app.services.report_job_runner import spawn_sales_report_job
from app.services.report_storage import create_report_job, delete_report_job, get_report_job

router = APIRouter(prefix="/reports", tags=["reports"])


def _job_status_response(job, *, status_code: int, error: str | None = None) -> JSONResponse:
    body = SalesReportJobStatusResponse(
        reportId=job.id,
        status=job.status,
        expiresAt=job.expires_at,
        error=error or job.error_message,
    )
    return JSONResponse(status_code=status_code, content=jsonable_encoder(body))


@router.post("/sales", status_code=status.HTTP_202_ACCEPTED)
async def create_sales_report(
    request: Request,
    body: SalesReportCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Enqueue a sales report job. Poll GET /reports/sales/{reportId} until ready."""
    request.state.user_id = user.id

    try:
        validate_move_type(body.move_type)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    callback_url: str | None = None
    if body.callback_url is not None:
        try:
            callback_url = validate_callback_url(body.callback_url)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    params = normalize_sales_report_params(
        move_type=body.move_type,
        start=body.start,
        end=body.end,
        location=body.location,
        goal=body.goal,
        sales_rep_name=body.sales_rep_name,
        default_filter=body.default_filter,
        callback_url=callback_url,
    )
    job = await create_report_job(db, user_id=user.id, params=params)
    spawn_sales_report_job(job.id, user.id)

    response_body = SalesReportJobCreatedResponse(
        reportId=job.id,
        status=job.status,
        expiresAt=job.expires_at,
    )
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=jsonable_encoder(response_body),
    )


@router.get("/sales/{report_id}")
async def get_sales_report(
    request: Request,
    report_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a ready report or receive status while the job is still running."""
    request.state.user_id = user.id

    job = await get_report_job(db, report_id, user_id=user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    now = datetime.now(UTC)
    if job.expires_at <= now:
        await delete_report_job(db, job)
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Report expired")

    if job.status in ("pending", "running"):
        return _job_status_response(job, status_code=status.HTTP_409_CONFLICT)

    if job.status == "failed":
        return _job_status_response(job, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if job.status != "ready" or not job.file_path:
        return _job_status_response(job, status_code=status.HTTP_409_CONFLICT)

    return FileResponse(
        job.file_path,
        media_type="text/html",
        filename=job.filename,
    )
