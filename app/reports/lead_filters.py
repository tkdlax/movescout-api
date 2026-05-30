from typing import Any

from app.movescout.filters import build_date_range_filter, build_kendo_filter

VALID_MOVE_TYPES = frozenset(
    {"Interstate", "International", "Cross Border", "Alaska", "Hawaii", "Local/Intra"}
)

MOVE_TYPE_LABEL_TO_ID: dict[str, int] = {
    "Interstate": 119,
    "International": 124,
    "Cross Border": 125,
    "Alaska": 128,
    "Hawaii": 129,
    "Local/Intra": 130,
}


def validate_move_type(move_type: str) -> None:
    if move_type not in VALID_MOVE_TYPES:
        raise ValueError(
            f"Unknown move_type: {move_type}. "
            f"Valid values: {', '.join(sorted(VALID_MOVE_TYPES))}"
        )


def build_report_lead_filters(
    *,
    start: str,
    end: str,
    move_type: str,
    sales_rep_name: str | None = None,
) -> list[dict[str, Any]]:
    """Build GetAllLead filters for the sales report (date range + upstream move type)."""
    validate_move_type(move_type)
    move_type_id = MOVE_TYPE_LABEL_TO_ID[move_type]

    filters: list[dict[str, Any]] = [
        build_date_range_filter("creationTime", start, end),
        build_kendo_filter("moveTypeId", "eq", move_type_id),
    ]

    if sales_rep_name:
        filters.append(build_kendo_filter("salesRepName", "contains", sales_rep_name))

    return filters
