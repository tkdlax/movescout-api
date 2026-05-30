from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.reports.lead_filters import (
    MOVE_TYPE_LABEL_TO_ID,
    build_report_lead_filters,
    validate_move_type,
)
from app.reports.sales_data import (
    ReportTooManyLeadsError,
    fetch_leads_for_report,
    transform_leads_to_rows,
)
from app.reports.sales_report import bucket, build_html, tally, week_start


def test_validate_move_type_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown move_type"):
        validate_move_type("Residential")


def test_build_report_lead_filters_includes_move_type_and_dates():
    filters = build_report_lead_filters(
        start="Jan 1, 2026",
        end="May 29, 2026",
        move_type="Interstate",
        sales_rep_name="Jacob",
    )
    assert len(filters) == 3
    fields = {f["field"] for f in filters}
    assert fields == {"creationTime", "moveTypeId", "salesRepName"}
    move_filter = next(f for f in filters if f["field"] == "moveTypeId")
    assert move_filter["value"] == MOVE_TYPE_LABEL_TO_ID["Interstate"]
    assert move_filter["operator"] == "eq"


def test_transform_leads_to_rows_filters_by_move_type():
    leads = [
        {
            "moveTypeId": 119,
            "dispositionId": 38,
            "salesRepName": "Alice",
            "creationTime": "2026-03-10T12:00:00Z",
        },
        {
            "moveTypeId": 130,
            "dispositionId": 43,
            "salesRepName": "Bob",
            "creationTime": "2026-03-11T12:00:00Z",
        },
    ]
    rows = transform_leads_to_rows(leads, "Interstate")
    assert len(rows) == 1
    assert rows[0]["rep"] == "Alice"
    assert rows[0]["bucket"] == "Booked"
    assert rows[0]["week"] == datetime(2026, 3, 10, tzinfo=UTC).isocalendar()[1]


def test_transform_leads_unassigned_rep():
    leads = [
        {
            "moveTypeId": 119,
            "dispositionId": 44,
            "salesRepName": "   ",
            "creationTime": "2026-01-05T10:00:00Z",
        }
    ]
    rows = transform_leads_to_rows(leads, "Interstate")
    assert rows[0]["rep"] == "Unassigned"
    assert rows[0]["bucket"] == "Pending"


def test_bucket_mapping():
    assert bucket("Booked") == "Booked"
    assert bucket("Ready to book") == "Ready to Book"
    assert bucket("Survey Scheduled") == "Survey Scheduled"
    assert bucket("New") == "Pending"


def test_week_start_cross_platform():
    assert week_start(1, 2026) == "12/29/25"
    assert week_start(10, 2026) == "3/2/26"


def test_build_html_contains_fiscal_year_and_rep():
    rows = [
        {"rep": "Alice", "week": 10, "year": 2026, "disp": "Booked", "bucket": "Booked"},
        {"rep": "Alice", "week": 11, "year": 2026, "disp": "New", "bucket": "Pending"},
    ]
    html = build_html(rows, "Interstate", "Test Location", 0.40, fiscal_year=2026)
    assert "Test Location" in html
    assert "Fiscal Year 2026" in html
    assert "Alice" in html
    assert "TOTAL WEEKLY LEADS — 2026" in html
    assert "<!DOCTYPE html>" in html


def test_tally_aggregates_by_rep_week_bucket():
    rows = [
        {"rep": "Alice", "week": 1, "year": 2026, "disp": "Booked", "bucket": "Booked"},
        {"rep": "Alice", "week": 1, "year": 2026, "disp": "Booked", "bucket": "Booked"},
        {"rep": "Alice", "week": 1, "year": 2026, "disp": "New", "bucket": "Pending"},
    ]
    result = tally(rows)
    assert result["Alice"][1]["Booked"] == 2
    assert result["Alice"][1]["Pending"] == 1


@pytest.mark.asyncio
async def test_fetch_leads_for_report_raises_when_over_max():
    client = AsyncMock()
    with patch(
        "app.reports.sales_data.probe_leads_total_count",
        new=AsyncMock(return_value=5000),
    ):
        with pytest.raises(ReportTooManyLeadsError, match="5000"):
            await fetch_leads_for_report(
                client,
                start="Jan 1, 2026",
                end="May 29, 2026",
                move_type="Interstate",
                max_leads=2500,
            )


@pytest.mark.asyncio
async def test_fetch_leads_for_report_returns_empty_when_no_leads():
    client = AsyncMock()
    with patch(
        "app.reports.sales_data.probe_leads_total_count",
        new=AsyncMock(return_value=0),
    ):
        leads, total = await fetch_leads_for_report(
            client,
            start="Jan 1, 2026",
            end="May 29, 2026",
            move_type="Interstate",
        )
    assert leads == []
    assert total == 0
