"""Extract Shape A pricing summary columns from estimate pricing JSON."""

from __future__ import annotations

import json
from typing import Any

# Canonical net-total fields from GetEstimatePricingTotalJsonResponse.
CANONICAL_NET_FIELDS: dict[str, str] = {
    "totalTransportationNet": "totalTransportationChargesNet",
    "totalContainersNet": "totalContainerChargesNet",
    "totalPackingNet": "totalPackingChargesNet",
    "totalUnpackingNet": "totalUnpackingChargesNet",
    "totalCratingNet": "cratingChargesNet",
    "totalUncratingNet": "unCratingChargesNet",
    "totalBulkiesNet": "bulkiesChargesNet",
    "totalMiscellaneousNet": "miscellaneousChargesNet",
    "totalAccessorialsNet": "accessorialsChargesNet",
    "totalSitOriginNet": "sitOriginChargesNet",
    "totalSitDestinationNet": "sitDestinationChargesNet",
    "totalAutoSpotNet": "autoSpotNet",
    "totalEstimatePriceNet": "totalEstimatinPriceNet",
}

PRICING_META_COLUMNS = ("hasPrimaryEstimate", "estimateId", "estimateName", "pricingFetchError")

PRICING_SUB_FIELD_COLUMNS = (
    "lineHaulNet",
    "totalWeight",
    "smfPercentage",
    "selectedValuation",
)

PRICING_SUMMARY_COLUMNS = (
    *PRICING_META_COLUMNS,
    *CANONICAL_NET_FIELDS.keys(),
    *PRICING_SUB_FIELD_COLUMNS,
)


def _coerce_number(value: Any) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _net_amount(value: Any) -> float | int:
    coerced = _coerce_number(value)
    return coerced if coerced is not None else 0


def resolve_pricing_payload(response: dict[str, Any]) -> dict[str, Any]:
    """Normalize middleware/pricing response to the inner pricing object."""
    raw = response.get("pricingResponseJson")
    if isinstance(raw, str):
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    if isinstance(raw, dict):
        return raw
    if response.get("transportationSubItemCharges") is not None:
        return response
    return response


def _json_key_to_column(key: str) -> str:
    """Map an unknown *Net / *ChargesNet JSON key to a CSV column name."""
    if key in CANONICAL_NET_FIELDS.values():
        for column, source in CANONICAL_NET_FIELDS.items():
            if source == key:
                return column
    if key.endswith("ChargesNet"):
        prefix = key[: -len("ChargesNet")]
    elif key.endswith("Net"):
        prefix = key[: -len("Net")]
    else:
        return f"total{key[0].upper()}{key[1:]}"
    if prefix.startswith("total"):
        base = prefix[5:]
    else:
        base = prefix
    if not base:
        return f"total{key}"
    return f"total{base[0].upper()}{base[1:]}Net"


def fill_dynamic_net_columns(
    summary: dict[str, Any],
    pricing: dict[str, Any],
    dynamic_columns: list[str],
) -> dict[str, Any]:
    """Ensure dynamically discovered net columns are present on a summary row."""
    result = dict(summary)
    for column in dynamic_columns:
        if column in result:
            continue
        source_keys = [
            key
            for key in pricing
            if isinstance(key, str) and _json_key_to_column(key) == column
        ]
        if source_keys:
            result[column] = _net_amount(pricing.get(source_keys[0]))
        else:
            result[column] = 0
    return result


def discover_dynamic_net_columns(pricing_objects: list[dict[str, Any]]) -> list[str]:
    """Return extra column names for *Net keys not in the canonical map."""
    known_sources = set(CANONICAL_NET_FIELDS.values())
    discovered: set[str] = set()
    for pricing in pricing_objects:
        for key, value in pricing.items():
            if not isinstance(key, str):
                continue
            if not (key.endswith("Net") or key.endswith("ChargesNet")):
                continue
            if key in known_sources:
                continue
            if _coerce_number(value) is None:
                continue
            discovered.add(_json_key_to_column(key))
    return sorted(discovered)


def extract_selected_valuation(pricing: dict[str, Any]) -> str | None:
    charges = pricing.get("valuationCharges")
    if not isinstance(charges, list):
        return None
    for item in charges:
        if not isinstance(item, dict):
            continue
        if item.get("isSelected"):
            value = item.get("valuationType")
            return str(value) if value is not None else None
    return None


def pricing_summary_from_json(
    pricing: dict[str, Any],
    *,
    estimate_id: Any = None,
    estimate_name: str | None = None,
) -> dict[str, Any]:
    """Extract summary columns when a primary estimate exists."""
    summary: dict[str, Any] = {
        "hasPrimaryEstimate": True,
        "estimateId": estimate_id,
        "estimateName": estimate_name,
        "pricingFetchError": None,
    }

    for column, source_key in CANONICAL_NET_FIELDS.items():
        summary[column] = _net_amount(pricing.get(source_key))

    for key, value in pricing.items():
        if not isinstance(key, str):
            continue
        if key in CANONICAL_NET_FIELDS.values():
            continue
        if not (key.endswith("Net") or key.endswith("ChargesNet")):
            continue
        if _coerce_number(value) is None:
            continue
        summary[_json_key_to_column(key)] = _net_amount(value)

    transport = pricing.get("transportationSubItemCharges")
    if isinstance(transport, dict):
        summary["lineHaulNet"] = _net_amount(transport.get("lineHaulChargesNet"))
        weight = _coerce_number(transport.get("totalWeight"))
        summary["totalWeight"] = weight if weight is not None else 0
        smf = _coerce_number(transport.get("smfPercentage"))
        summary["smfPercentage"] = smf if smf is not None else 0
    else:
        summary["lineHaulNet"] = 0
        summary["totalWeight"] = 0
        summary["smfPercentage"] = 0

    summary["selectedValuation"] = extract_selected_valuation(pricing)
    return summary


def empty_pricing_summary(
    *,
    has_primary_estimate: bool = False,
    estimate_id: Any = None,
    estimate_name: str | None = None,
    pricing_fetch_error: str | None = None,
) -> dict[str, Any]:
    """Pricing columns for leads without an estimate or failed pricing fetch."""
    summary: dict[str, Any] = {
        "hasPrimaryEstimate": has_primary_estimate,
        "estimateId": estimate_id,
        "estimateName": estimate_name,
        "pricingFetchError": pricing_fetch_error,
    }
    for column in CANONICAL_NET_FIELDS:
        summary[column] = None
    for column in PRICING_SUB_FIELD_COLUMNS:
        summary[column] = None
    return summary


def pricing_summary_from_response(response: dict[str, Any]) -> dict[str, Any]:
    """Build summary from GET /leads/{id}/pricing middleware response."""
    estimate_id = response.get("estimateId")
    estimate_name = response.get("estimateName")
    pricing = resolve_pricing_payload(response)
    return pricing_summary_from_json(
        pricing,
        estimate_id=estimate_id,
        estimate_name=estimate_name if isinstance(estimate_name, str) else None,
    )
