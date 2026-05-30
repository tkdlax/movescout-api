from datetime import UTC, datetime
from typing import Any

from app.movescout.client import MoveScoutClient
from app.movescout.pagination import fetch_all_leads_paginated, probe_leads_total_count
from app.reports.lead_filters import MOVE_TYPE_LABEL_TO_ID, build_report_lead_filters
from app.reports.sales_report import DISPOSITION_MAP, MOVE_TYPE_MAP, bucket


class ReportTooManyLeadsError(Exception):
    def __init__(self, total: int, max_leads: int) -> None:
        self.total = total
        self.max_leads = max_leads
        super().__init__(
            f"Report query matched {total} leads, exceeding the limit of {max_leads}. "
            "Narrow the date range or add filters (e.g. salesRepName)."
        )


def _parse_creation_time(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _resolve_move_type_label(lead: dict[str, Any]) -> str:
    move_type_id = lead.get("moveTypeId")
    if move_type_id is not None:
        try:
            return MOVE_TYPE_MAP.get(int(move_type_id), "")
        except (TypeError, ValueError):
            pass
    raw = lead.get("moveType")
    return raw.strip() if isinstance(raw, str) else ""


def _resolve_disposition_label(lead: dict[str, Any]) -> str:
    disposition_id = lead.get("dispositionId")
    if disposition_id is not None:
        try:
            return DISPOSITION_MAP.get(int(disposition_id), "")
        except (TypeError, ValueError):
            pass
    raw = lead.get("disposition")
    return raw.strip() if isinstance(raw, str) else ""


def transform_leads_to_rows(leads: list[dict[str, Any]], move_type: str) -> list[dict[str, Any]]:
    """Resolve IDs, apply post-fetch move_type safety net, and shape rows for build_html."""
    expected_id = MOVE_TYPE_LABEL_TO_ID.get(move_type)
    rows: list[dict[str, Any]] = []

    for lead in leads:
        mt = _resolve_move_type_label(lead)
        move_type_id = lead.get("moveTypeId")

        matches = mt == move_type
        if not matches and expected_id is not None and move_type_id is not None:
            try:
                matches = int(move_type_id) == expected_id
            except (TypeError, ValueError):
                pass

        if not matches:
            continue

        creation = lead.get("creationTime") or lead.get("createdDate")
        if not creation:
            continue

        dt = _parse_creation_time(creation)
        disp = _resolve_disposition_label(lead)
        rep = (lead.get("salesRepName") or lead.get("salesRep") or "").strip() or "Unassigned"

        rows.append(
            {
                "rep": rep,
                "week": dt.isocalendar()[1],
                "year": dt.year,
                "disp": disp,
                "bucket": bucket(disp),
            }
        )

    return [row for row in rows if row["week"]]


async def fetch_leads_for_report(
    client: MoveScoutClient,
    *,
    start: str,
    end: str,
    move_type: str,
    default_filter: int = 3,
    sales_rep_name: str | None = None,
    page_size: int = 500,
    max_leads: int | None = None,
) -> tuple[list[dict[str, Any]], int]:
    filters = build_report_lead_filters(
        start=start,
        end=end,
        move_type=move_type,
        sales_rep_name=sales_rep_name,
    )

    total = await probe_leads_total_count(
        client,
        default_filter=default_filter,
        filters=filters,
    )
    if total <= 0:
        return [], 0

    if max_leads is not None and total > max_leads:
        raise ReportTooManyLeadsError(total, max_leads)

    leads, _ = await fetch_all_leads_paginated(
        client,
        default_filter=default_filter,
        filters=filters,
        page_size=page_size,
    )
    return leads, total
