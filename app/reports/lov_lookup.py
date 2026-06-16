"""Build LOV id→name lookups from MoveScout list-of-values payloads."""

from __future__ import annotations

from typing import Any

from app.services.csv_export import resolve_name_fields

# MoveScout tableName values from GetAllListofvalues → lead *Id field base names.
TABLE_NAME_TO_FIELD_BASE: dict[str, str] = {
    "Move_Type": "moveType",
    "Disposition LOVs": "disposition",
    "Detail Disposition LOVs": "lostReason",
    "SHIPPER_TYPE": "shipperType",
    "LEAD_TYPE": "leadType",
    "Dwelling_Type": "dwellingType",
    "Furnish Level LOVs": "furnishLevel",
    "APPOINTMENT": "appointmentType",
    "BILLING_TYPE": "billingType",
    "Estimate_Type": "estimateType",
    "FUNDED": "funded",
    "MKT_CHNL": "marketingChannel",
    "OWN_OR_RENT": "ownOrRent",
    "PHONE_TYPE": "phoneType",
    "SOURCE_NAME": "sourceName",
}


def _extract_lov_items(lov_payload: Any) -> list[dict[str, Any]]:
    """Normalize middleware /lov or raw MoveScout result to a flat item list."""
    if isinstance(lov_payload, list):
        return [item for item in lov_payload if isinstance(item, dict)]

    if not isinstance(lov_payload, dict):
        return []

    items = lov_payload.get("items")
    if isinstance(items, list):
        return [item for item in items if isinstance(item, dict)]

    # Cached bad shape from pre-fix POST calls: {"items": {}} — treat as empty.
    if isinstance(items, dict):
        return []

    # Upstream result object without middleware normalization.
    if "tableName" in lov_payload and "id" in lov_payload:
        return [lov_payload]

    return []


def _field_base_for_table(table_name: str) -> str | None:
    if table_name in TABLE_NAME_TO_FIELD_BASE:
        return TABLE_NAME_TO_FIELD_BASE[table_name]
    return None


def _store_lookup_entry(lookup: dict[str, dict[Any, str]], field_base: str, entry_id: Any, name: str) -> None:
    bucket = lookup.setdefault(field_base, {})
    bucket[entry_id] = name
    try:
        bucket[int(entry_id)] = name
    except (TypeError, ValueError):
        pass
    bucket[str(entry_id)] = name


def build_lov_lookup(lov_payload: Any) -> dict[str, dict[Any, str]]:
    """Index LOV items as {fieldBase: {id: name}} for resolve_name_fields."""
    lookup: dict[str, dict[Any, str]] = {}

    for item in _extract_lov_items(lov_payload):
        table_name = item.get("tableName")
        entry_id = item.get("id")
        entry_name = item.get("name") or item.get("value")
        if not isinstance(table_name, str) or entry_id is None or not entry_name:
            continue

        field_base = _field_base_for_table(table_name.strip())
        if field_base is None:
            continue

        _store_lookup_entry(lookup, field_base, entry_id, str(entry_name).strip())

    return lookup


def resolve_lead_names(
    lead: dict[str, Any],
    lov_lookup: dict[str, dict[Any, str]] | None,
) -> dict[str, Any]:
    """Return a copy of the lead with null *Name fields filled from LOV."""
    if not lov_lookup:
        return dict(lead)
    return resolve_name_fields(lead, lov_lookup)
