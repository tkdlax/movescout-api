import logging
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.db import ReportJob
from app.reports.sales_params import (
    SalesReportParams,
    build_report_filename,
    sales_report_params_to_dict,
)

logger = logging.getLogger(__name__)


def ensure_storage_dir() -> Path:
    settings = get_settings()
    path = Path(settings.report_storage_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def report_file_path(report_id: uuid.UUID) -> Path:
    return ensure_storage_dir() / f"{report_id}.html"


def write_report_file(report_id: uuid.UUID, html: str) -> Path:
    path = report_file_path(report_id)
    path.write_text(html, encoding="utf-8")
    return path


def delete_report_file(file_path: str | None) -> None:
    if not file_path:
        return
    try:
        Path(file_path).unlink(missing_ok=True)
    except OSError as exc:
        logger.warning("Failed to delete report file %s: %s", file_path, exc)


async def create_report_job(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    params: SalesReportParams,
) -> ReportJob:
    settings = get_settings()
    now = datetime.now(UTC)
    job = ReportJob(
        user_id=user_id,
        status="pending",
        params=sales_report_params_to_dict(params),
        filename=build_report_filename(params),
        expires_at=now + timedelta(seconds=settings.report_ttl_seconds),
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


async def get_report_job(
    db: AsyncSession,
    report_id: uuid.UUID,
    *,
    user_id: uuid.UUID | None = None,
) -> ReportJob | None:
    result = await db.execute(select(ReportJob).where(ReportJob.id == report_id))
    job = result.scalar_one_or_none()
    if job is None:
        return None
    if user_id is not None and job.user_id != user_id:
        return None
    return job


async def delete_report_job(db: AsyncSession, job: ReportJob) -> None:
    delete_report_file(job.file_path)
    await db.delete(job)


async def sweep_expired_jobs(db: AsyncSession) -> int:
    now = datetime.now(UTC)
    result = await db.execute(select(ReportJob).where(ReportJob.expires_at < now))
    jobs = result.scalars().all()
    for job in jobs:
        delete_report_file(job.file_path)
        await db.delete(job)
    if jobs:
        await db.flush()
        logger.info("Swept %d expired report job(s)", len(jobs))
    return len(jobs)


async def sweep_expired_jobs_batch() -> int:
    from app.database import async_session_factory

    async with async_session_factory() as db:
        try:
            count = await sweep_expired_jobs(db)
            await db.commit()
            return count
        except Exception:
            await db.rollback()
            raise
