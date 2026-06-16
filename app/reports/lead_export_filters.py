"""Filter builders for lead export scripts."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.movescout.filters import build_date_range_filter


def _parse_date_input(value: str) -> date:
    text = value.strip()
    if not text:
        raise ValueError("Date value cannot be empty")

    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    # MoveScout UI style: "Jan 1, 2026"
    try:
        return datetime.strptime(text, "%b %d, %Y").date()
    except ValueError:
        pass
    try:
        return datetime.strptime(text, "%B %d, %Y").date()
    except ValueError:
        pass

    raise ValueError(
        f"Unrecognized date format: {value!r}. Use YYYY-MM-DD or 'Jan 1, 2026'."
    )


def format_movescout_date(value: date) -> str:
    """Format for MoveScout creationTime range filter (id=9)."""
    return f"{value.strftime('%b')} {value.day}, {value.year}"


def normalize_date_range(start: str, end: str) -> tuple[str, str]:
    start_date = _parse_date_input(start)
    end_date = _parse_date_input(end)
    if end_date < start_date:
        raise ValueError(f"end date {end!r} is before start date {start!r}")
    return format_movescout_date(start_date), format_movescout_date(end_date)


def build_creation_date_filters(start: str, end: str) -> list[dict[str, Any]]:
    """Build GetAllLead filters for creationTime between start and end (inclusive)."""
    start_fmt, end_fmt = normalize_date_range(start, end)
    return [build_date_range_filter("creationTime", start_fmt, end_fmt)]


def filters_to_query_param(filters: list[dict[str, Any]]) -> str:
    import json

    return json.dumps(filters, separators=(",", ":"))
