from datetime import UTC, datetime
from email.utils import format_datetime
from typing import Any

ALLOWED_FILTER_FIELDS = {
    "agencyCode",
    "dispositionId",
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


def build_kendo_filter(field: str, op: str, value: Any, condition: str = "and") -> dict[str, Any]:
    if field not in ALLOWED_FILTER_FIELDS:
        raise ValueError(f"Filter field '{field}' is not allowed")

    operator = OP_MAP.get(op.lower())
    if not operator:
        raise ValueError(f"Filter operator '{op}' is not supported")

    filter_obj: dict[str, Any] = {
        "field": field,
        "operator": operator,
        "condition": condition,
        "date": current_http_date(),
    }

    if operator == "isnull":
        filter_obj["value"] = None
    elif operator == "isnotnull":
        filter_obj["value"] = None
    else:
        filter_obj["value"] = value

    return filter_obj


def build_filters(filters: list[dict[str, Any]], logic: str = "and") -> list[dict[str, Any]]:
    if not filters:
        return []

    result: list[dict[str, Any]] = []
    for i, f in enumerate(filters):
        condition = logic if i > 0 else "and"
        result.append(
            build_kendo_filter(
                field=f["field"],
                op=f["op"],
                value=f.get("value"),
                condition=condition,
            )
        )
    return result


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
    return {
        "field": field,
        "operator": "eq",
        "value": {"id": 6, "value": days},
        "condition": "and",
        "date": current_http_date(),
    }
