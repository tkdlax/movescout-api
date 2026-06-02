import asyncio
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.config import get_settings
from app.database import async_session_factory
from app.models.db import ReportJob, User
from app.movescout.client import MoveScoutError
from app.reports.lead_filters import validate_move_type
from app.reports.sales_data import (
    ReportTooManyLeadsError,
    fetch_leads_for_report,
    transform_leads_to_rows,
)
from app.reports.sales_params import sales_report_params_from_dict
from app.reports.sales_report import build_html
from app.services.movescout_service import with_movescout_client
from app.services.report_callback import notify_report_callback
from app.services.report_storage import delete_report_file, write_report_file

logger = logging.getLogger(__name__)


async def _notify_if_configured(job: ReportJob) -> None:
    callback_url = job.params.get("callback_url") if job.params else None
    if not callback_url:
        return
    await notify_report_callback(
        callback_url=callback_url,
        report_id=job.id,
        status=job.status,
        expires_at=job.expires_at,
        filename=job.filename,
        error=job.error_message,
    )


async def _mark_failed(db, job: ReportJob, message: str) -> None:
    job.status = "failed"
    job.error_message = message
    job.completed_at = datetime.now(UTC)
    delete_report_file(job.file_path)
    job.file_path = None
    await db.commit()
    await _notify_if_configured(job)


async def run_sales_report_job(report_id: uuid.UUID, user_id: uuid.UUID) -> None:
    async with async_session_factory() as db:
        job = None
        for attempt in range(5):
            result = await db.execute(select(ReportJob).where(ReportJob.id == report_id))
            job = result.scalar_one_or_none()
            if job is not None:
                break
            if attempt < 4:
                await asyncio.sleep(0.2)

        if job is None or job.user_id != user_id:
            logger.error(
                "Report job %s not found for user %s; job may stay pending forever",
                report_id,
                user_id,
            )
            return

        job.status = "running"
        await db.commit()

        try:
            params = sales_report_params_from_dict(job.params)
            validate_move_type(params.move_type)
        except ValueError as exc:
            await _mark_failed(db, job, str(exc))
            return

        user_result = await db.execute(
            select(User).where(User.id == user_id, User.is_active.is_(True))
        )
        user = user_result.scalar_one_or_none()
        if user is None:
            await _mark_failed(db, job, "User not found or inactive")
            return

        settings = get_settings()

        async def generate(client):
            return await fetch_leads_for_report(
                client,
                start=params.start,
                end=params.end,
                move_type=params.move_type,
                default_filter=params.default_filter,
                sales_rep_name=params.sales_rep_name,
                page_size=settings.export_page_size,
                max_leads=settings.report_max_leads,
            )

        try:
            leads, _total = await with_movescout_client(db, user, generate)
        except ReportTooManyLeadsError as exc:
            await _mark_failed(db, job, str(exc))
            return
        except MoveScoutError as exc:
            await _mark_failed(db, job, exc.message)
            return
        except Exception as exc:
            logger.exception("Report job %s failed during lead fetch", report_id)
            await _mark_failed(db, job, f"{type(exc).__name__}: {exc}")
            return

        rows = transform_leads_to_rows(leads, params.move_type)
        if not rows:
            await _mark_failed(db, job, "No leads found for the given filters and move type")
            return

        try:
            html = await asyncio.to_thread(
                build_html,
                rows,
                params.move_type,
                params.location,
                params.goal,
                params.fiscal_year,
            )
            path = write_report_file(report_id, html)
        except Exception as exc:
            logger.exception("Report job %s failed during HTML build", report_id)
            await _mark_failed(db, job, f"{type(exc).__name__}: {exc}")
            return

        await db.refresh(job)
        job.status = "ready"
        job.file_path = str(path)
        job.completed_at = datetime.now(UTC)
        job.error_message = None
        await db.commit()
        logger.info("Report job %s ready at %s", report_id, path)
        await _notify_if_configured(job)


def spawn_sales_report_job(report_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Deprecated: use FastAPI BackgroundTasks from the route to avoid commit races."""
    task = asyncio.create_task(run_sales_report_job(report_id, user_id))

    def _log_task_result(finished: asyncio.Task) -> None:
        try:
            finished.result()
        except Exception:
            logger.exception("Unhandled error in report job task %s", report_id)

    task.add_done_callback(_log_task_result)
