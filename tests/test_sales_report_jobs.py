import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.api_key import get_current_user, get_current_user_header_or_query
from app.database import get_db
from app.main import app
from app.models.db import ReportJob
from app.reports.sales_data import ReportTooManyLeadsError
from app.reports.sales_params import normalize_sales_report_params
from app.services.report_callback import build_report_download_url, validate_callback_url
from app.services.report_job_runner import run_sales_report_job
from app.services.report_storage import sweep_expired_jobs, write_report_file


@pytest.fixture
def test_user_id():
    return uuid.uuid4()


@pytest.fixture
def override_auth(test_user_id):
    user = SimpleNamespace(id=test_user_id, is_active=True)

    async def _override_user():
        return user

    async def _override_db():
        session = AsyncMock()
        yield session

    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_current_user_header_or_query] = _override_user
    app.dependency_overrides[get_db] = _override_db
    yield user
    app.dependency_overrides.clear()


def test_normalize_sales_report_params_defaults():
    params = normalize_sales_report_params(move_type="Interstate")
    assert params.move_type == "Interstate"
    assert "Jan 1" in params.start
    assert params.default_filter == 3


@pytest.mark.asyncio
async def test_create_report_job_returns_202(override_auth, test_user_id):
    report_id = uuid.uuid4()
    expires_at = datetime.now(UTC) + timedelta(hours=1)
    mock_job = SimpleNamespace(
        id=report_id,
        status="pending",
        expires_at=expires_at,
    )

    with patch("app.routes.reports.create_report_job", new=AsyncMock(return_value=mock_job)):
        with patch("app.routes.reports.run_sales_report_job", new=AsyncMock()) as run_job:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/reports/sales",
                    headers={"X-API-Key": "test-key"},
                    json={"moveType": "Interstate"},
                )

    assert response.status_code == 202
    body = response.json()
    assert body["reportId"] == str(report_id)
    assert body["status"] == "pending"
    run_job.assert_awaited_once_with(report_id, test_user_id)


@pytest.mark.asyncio
async def test_create_report_job_invalid_move_type(override_auth):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/reports/sales",
            headers={"X-API-Key": "test-key"},
            json={"moveType": "Residential"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_report_not_found(override_auth):
    with patch("app.routes.reports.get_report_job", new=AsyncMock(return_value=None)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/reports/sales/{uuid.uuid4()}",
                headers={"X-API-Key": "test-key"},
            )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_report_running_returns_409(override_auth):
    job = SimpleNamespace(
        id=uuid.uuid4(),
        status="running",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        error_message=None,
    )
    with patch("app.routes.reports.get_report_job", new=AsyncMock(return_value=job)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/reports/sales/{job.id}",
                headers={"X-API-Key": "test-key"},
            )
    assert response.status_code == 409
    assert response.json()["status"] == "running"


@pytest.mark.asyncio
async def test_get_report_ready_returns_file(override_auth, tmp_path):
    report_id = uuid.uuid4()
    html_path = tmp_path / f"{report_id}.html"
    html_path.write_text("<html>ready</html>", encoding="utf-8")
    job = SimpleNamespace(
        id=report_id,
        status="ready",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        file_path=str(html_path),
        filename="sales-interstate-20260529.html",
        error_message=None,
    )
    with patch("app.routes.reports.get_report_job", new=AsyncMock(return_value=job)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/reports/sales/{report_id}",
                headers={"X-API-Key": "test-key"},
            )
    assert response.status_code == 200
    assert "ready" in response.text
    assert response.headers["content-type"].startswith("text/html")


@pytest.mark.asyncio
async def test_get_report_expired_returns_410(override_auth):
    job = MagicMock()
    job.id = uuid.uuid4()
    job.status = "ready"
    job.expires_at = datetime.now(UTC) - timedelta(minutes=5)
    job.file_path = "/tmp/expired.html"

    with patch("app.routes.reports.get_report_job", new=AsyncMock(return_value=job)):
        with patch("app.routes.reports.delete_report_job", new=AsyncMock()) as delete_job:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    f"/reports/sales/{job.id}",
                    headers={"X-API-Key": "test-key"},
                )

    assert response.status_code == 410
    delete_job.assert_awaited_once()


@pytest.mark.asyncio
async def test_runner_marks_failed_on_too_many_leads(test_user_id, tmp_path):
    report_id = uuid.uuid4()
    job = ReportJob(
        id=report_id,
        user_id=test_user_id,
        status="pending",
        params={
            "move_type": "Interstate",
            "start": "Jan 1, 2026",
            "end": "May 29, 2026",
            "location": "Test",
            "goal": 0.4,
            "sales_rep_name": None,
            "default_filter": 3,
            "fiscal_year": 2026,
        },
        filename="sales-interstate-20260529.html",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    user = SimpleNamespace(id=test_user_id, is_active=True)

    mock_db = AsyncMock()
    job_result = MagicMock()
    job_result.scalar_one_or_none.return_value = job
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = user
    mock_db.execute = AsyncMock(side_effect=[job_result, user_result])
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    async def fail_movescout(*_args, **_kwargs):
        raise ReportTooManyLeadsError(5000, 2500)

    with patch("app.services.report_job_runner.async_session_factory") as factory:
        factory.return_value.__aenter__.return_value = mock_db
        with patch(
            "app.services.report_job_runner.with_movescout_client",
            new=AsyncMock(side_effect=fail_movescout),
        ):
            await run_sales_report_job(report_id, test_user_id)

    assert job.status == "failed"
    assert "5000" in (job.error_message or "")


@pytest.mark.asyncio
async def test_sweep_expired_deletes_file_and_row(tmp_path):
    report_id = uuid.uuid4()
    path = tmp_path / f"{report_id}.html"
    path.write_text("<html></html>", encoding="utf-8")

    job = ReportJob(
        id=report_id,
        user_id=uuid.uuid4(),
        status="ready",
        params={"move_type": "Interstate"},
        file_path=str(path),
        filename="sales.html",
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )

    mock_db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [job]
    mock_db.execute = AsyncMock(return_value=result)
    mock_db.delete = AsyncMock()
    mock_db.flush = AsyncMock()

    count = await sweep_expired_jobs(mock_db)

    assert count == 1
    assert not path.exists()
    mock_db.delete.assert_awaited_once_with(job)


def test_write_report_file(tmp_path):
    report_id = uuid.uuid4()
    with patch("app.services.report_storage.ensure_storage_dir", return_value=tmp_path):
        path = write_report_file(report_id, "<html>test</html>")
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "<html>test</html>"


def test_validate_callback_url_rejects_localhost():
    with pytest.raises(ValueError, match="localhost"):
        validate_callback_url("https://localhost/hook")


def test_validate_callback_url_rejects_private_ip():
    with pytest.raises(ValueError, match="private"):
        validate_callback_url("https://192.168.1.10/hook")


def test_build_report_download_url_uses_public_base():
    report_id = uuid.uuid4()
    with patch("app.services.report_callback.get_settings") as settings:
        settings.return_value.api_public_base_url = "https://mspapi.jbeckstead.com"
        url = build_report_download_url(report_id)
    assert url == f"https://mspapi.jbeckstead.com/reports/sales/{report_id}"


def test_validate_callback_url_accepts_https_host():
    assert validate_callback_url("https://example.webhook.office.com/abc") == (
        "https://example.webhook.office.com/abc"
    )


@pytest.mark.asyncio
async def test_create_report_job_rejects_bad_callback(override_auth):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/reports/sales",
            headers={"X-API-Key": "test-key"},
            json={"moveType": "Interstate", "callbackUrl": "https://127.0.0.1/hook"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_runner_notifies_callback_on_ready(test_user_id):
    report_id = uuid.uuid4()
    job = ReportJob(
        id=report_id,
        user_id=test_user_id,
        status="pending",
        params={
            "move_type": "Interstate",
            "start": "Jan 1, 2026",
            "end": "May 29, 2026",
            "location": "Test",
            "goal": 0.4,
            "sales_rep_name": None,
            "default_filter": 3,
            "fiscal_year": 2026,
            "callback_url": "https://hooks.example.com/report-done",
        },
        filename="sales-interstate-20260529.html",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    user = SimpleNamespace(id=test_user_id, is_active=True)

    mock_db = AsyncMock()
    job_result = MagicMock()
    job_result.scalar_one_or_none.return_value = job
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = user
    mock_db.execute = AsyncMock(side_effect=[job_result, user_result])
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    lead = {
        "moveTypeId": 119,
        "dispositionId": 38,
        "creationTime": "2026-03-10T12:00:00Z",
        "salesRepName": "Alice",
    }

    with patch("app.services.report_job_runner.async_session_factory") as factory:
        factory.return_value.__aenter__.return_value = mock_db
        with patch(
            "app.services.report_job_runner.with_movescout_client",
            new=AsyncMock(return_value=([lead], 1)),
        ):
            with patch(
                "app.services.report_job_runner.write_report_file",
                return_value=Path("/tmp/x.html"),
            ):
                with patch(
                    "app.services.report_job_runner._notify_if_configured",
                    new=AsyncMock(),
                ) as notify:
                    await run_sales_report_job(report_id, test_user_id)

    assert job.status == "ready"
    notify.assert_awaited_once()

