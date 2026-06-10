from datetime import UTC, datetime
from email.utils import format_datetime
from typing import Any

ALLOWED_FILTER_FIELDS = {
    "agencyCode",
    "dispositionId",
    "moveTypeId",
    "salesRepName",
    "creationTime",
    "registrationNumber",
    "firstName",
    "lastName",
    "city",
    "state",
    "bookerName",
    "leadId",
    "activityStart",
    "activityType",
}

OP_MAP = {
    "eq": "eq",
    "contains": "contains",
    "isnull": "isnull",
    "isnotnull": "isnotnull",
    "gte": "gte",
    "lte": "lte",
    "gt": "gt",
    "lt": "lt",
}


def current_http_date() -> str:
    return format_datetime(datetime.now(UTC), usegmt=True)


def build_kendo_filter(
    field: str,
    op: str,
    value: Any,
    condition: str = "and",
    *,
    date: str | None = None,
) -> dict[str, Any]:
    if field not in ALLOWED_FILTER_FIELDS:
        raise ValueError(f"Filter field '{field}' is not allowed")

    operator = OP_MAP.get(op.lower())
    if not operator:
        raise ValueError(f"Filter operator '{op}' is not supported")

    filter_obj: dict[str, Any] = {
        "field": field,
        "operator": operator,
        "condition": condition,
        "date": date or current_http_date(),
    }

    if operator == "isnull":
        filter_obj["value"] = None
    elif operator == "isnotnull":
        filter_obj["value"] = None
    else:
        filter_obj["value"] = value

    return filter_obj


def prepare_lead_filters(filters: list[dict[str, Any]], logic: str = "and") -> list[dict[str, Any]]:
    """Normalize caller filters to the exact GetAllLead filter objects MoveScout expects."""
    if not filters:
        return []

    result: list[dict[str, Any]] = []
    for i, raw in enumerate(filters):
        condition = logic if i > 0 else "and"

        if "operator" in raw:
            field = raw.get("field")
            if field not in ALLOWED_FILTER_FIELDS:
                raise ValueError(f"Filter field '{field}' is not allowed")
            upstream = {
                "field": field,
                "operator": raw["operator"],
                "value": raw.get("value"),
                "condition": raw.get("condition", condition),
                "date": raw.get("date") or current_http_date(),
            }
            result.append(upstream)
            continue

        field = raw.get("field")
        op = raw.get("op")
        if not field or not op:
            raise ValueError("Each filter requires field and op (or operator for passthrough)")

        result.append(
            build_kendo_filter(
                field,
                op,
                raw.get("value"),
                raw.get("condition", condition),
                date=raw.get("date"),
            )
        )
    return result


def build_filters(filters: list[dict[str, Any]], logic: str = "and") -> list[dict[str, Any]]:
    return prepare_lead_filters(filters, logic)


def build_date_range_filter(field: str, start: str, end: str) -> dict[str, Any]:
    return {
        "field": field,
        "operator": "eq",
        "value": {
            "id": 9,
            "value": {"start": start, "end": end},
        },
        "condition": "and",
        "date": current_http_date(),
    }


def build_last_n_days_filter(field: str, days: int) -> dict[str, Any]:
    """Relative 'last N days' preset (MoveScout UI uses id=8, string value)."""
    return {
        "field": field,
        "operator": "eq",
        "value": {"id": 8, "value": str(days)},
        "condition": "and",
        "date": current_http_date(),
    }
