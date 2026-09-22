from datetime import UTC, datetime
from email.utils import format_datetime
from typing import Any

ALLOWED_FILTER_FIELDS = {
    # Legacy middleware fields
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
    # P11 live-captured filter fields (2026-09-22)
    "id",  # Record Id (contains)
    "leadCustomerDetail.lastName",  # Last Name (contains)
    "leadCustomerDetail.firstName",  # First Name (contains)
    "leadCustomerDetail.primaryEmailAddress",  # Primary Email (contains)
    "leadcustomerdetail.homephone",  # Exact wire spelling; UI Phone Type quirk (contains)
    "assignedDate",  # Date preset {id, value}
    # P11 expanded live-proven fields (2026-09-22)
    "leadLMP.lmpId",  # LMP ID (contains)
    "appointmentTypeId",  # Appointment Type (eq)
    "leadMoveDate.loadFromDate",  # Load From Date - date preset {id, value}
    "primaryLeadEstimate.effectiveDate",  # Effective Date - date preset {id, value}
    "validThruDate",  # Valid Thru Date - date preset {id, value}
    "lastModificationTime",  # Last Modified - date preset {id, value}
    "mobileSyncFlag",  # Mobile Sync Flag (eq true)
    "isQualifiedLead",  # Is Qualified Lead (eq true)
    "createdUserName",  # Created By (contains)
    "estimateTotal",  # Estimate Total (eq numeric)
    "fundedId",  # Funded ID (eq)
    "dwellingTypeId",  # Dwelling Type (eq)
    "leadNonConforming.nonConformingFlag",  # Non-Conforming Flag (eq true)
    "leadMoSys.canadaGovMove",  # Canada Gov Move (eq true)
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


DATE_PRESET_FIELDS = {
    "assignedDate",
    "creationTime",
    "effectiveDate",
    "validThruDate",
    # P11 expanded date preset fields
    "leadMoveDate.loadFromDate",
    "primaryLeadEstimate.effectiveDate",
    "lastModificationTime",
}


def is_date_preset_value(value: Any) -> bool:
    """Check if value is a date preset object like {id: 5, value: 30}."""
    if not isinstance(value, dict):
        return False
    return "id" in value and "value" in value


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


# P11 Date Preset IDs (from live capture)
DATE_PRESET_PREVIOUS_MONTH = {"id": 5, "value": 30}


def build_previous_month_filter(field: str = "assignedDate") -> dict[str, Any]:
    """Previous Month date preset (id=5, value=30) as captured in P11."""
    return {
        "field": field,
        "operator": "eq",
        "value": DATE_PRESET_PREVIOUS_MONTH,
        "condition": "and",
        "date": current_http_date(),
    }
