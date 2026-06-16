"""Tests for pricing summary extraction."""

from app.reports.lead_export_filters import (
    build_creation_date_filters,
    normalize_date_range,
)
from app.reports.lov_lookup import build_lov_lookup, resolve_lead_names
from app.reports.pricing_summary import (
    discover_dynamic_net_columns,
    empty_pricing_summary,
    pricing_summary_from_json,
    pricing_summary_from_response,
    resolve_pricing_payload,
)


def _sample_pricing() -> dict:
    return {
        "totalTransportationChargesNet": 17457.84,
        "totalContainerChargesNet": 2429.35,
        "totalPackingChargesNet": 2009.2,
        "totalUnpackingChargesNet": 0,
        "miscellaneousChargesNet": 4795,
        "accessorialsChargesNet": 248.61,
        "totalEstimatinPriceNet": 26940,
        "transportationSubItemCharges": {
            "lineHaulChargesNet": 23377.2,
            "totalWeight": 17710,
            "smfPercentage": 25.28,
        },
        "valuationCharges": [
            {"valuationType": "$250 Deductible", "isSelected": False},
            {"valuationType": "Basic Coverage", "isSelected": True},
        ],
    }


def test_pricing_summary_from_json_extracts_totals_and_subfields():
    summary = pricing_summary_from_json(
        _sample_pricing(),
        estimate_id=2192413,
        estimate_name="Virginia Wakeland - May 26 2026",
    )

    assert summary["hasPrimaryEstimate"] is True
    assert summary["estimateId"] == 2192413
    assert summary["totalTransportationNet"] == 17457.84
    assert summary["totalPackingNet"] == 2009.2
    assert summary["totalUnpackingNet"] == 0
    assert summary["totalEstimatePriceNet"] == 26940
    assert summary["lineHaulNet"] == 23377.2
    assert summary["totalWeight"] == 17710
    assert summary["smfPercentage"] == 25.28
    assert summary["selectedValuation"] == "Basic Coverage"


def test_empty_pricing_summary_uses_nulls():
    summary = empty_pricing_summary(has_primary_estimate=False)
    assert summary["hasPrimaryEstimate"] is False
    assert summary["totalPackingNet"] is None
    assert summary["lineHaulNet"] is None
    assert summary["selectedValuation"] is None


def test_resolve_pricing_payload_from_string_json():
    inner = _sample_pricing()
    response = {"pricingResponseJson": '{"totalEstimatinPriceNet": 100}'}
    payload = resolve_pricing_payload(response)
    assert payload["totalEstimatinPriceNet"] == 100


def test_discover_dynamic_net_columns():
    pricing = dict(_sample_pricing())
    pricing["customWidgetChargesNet"] = 42
    columns = discover_dynamic_net_columns([pricing])
    assert "totalCustomWidgetNet" in columns


def test_pricing_summary_from_response_middleware_shape():
    response = {
        "leadId": 1553516,
        "estimateId": 2192413,
        "estimateName": "Test Estimate",
        **_sample_pricing(),
    }
    summary = pricing_summary_from_response(response)
    assert summary["estimateId"] == 2192413
    assert summary["totalPackingNet"] == 2009.2


def test_build_creation_date_filters_uses_id_9_range():
    filters = build_creation_date_filters("2026-01-01", "2026-05-29")
    assert len(filters) == 1
    creation = filters[0]
    assert creation["field"] == "creationTime"
    assert creation["value"]["id"] == 9
    assert creation["value"]["value"]["start"] == "Jan 1, 2026"
    assert creation["value"]["value"]["end"] == "May 29, 2026"


def test_normalize_date_range_accepts_movescout_format():
    start, end = normalize_date_range("Jan 1, 2026", "May 29, 2026")
    assert start == "Jan 1, 2026"
    assert end == "May 29, 2026"


def test_build_lov_lookup_and_resolve_lead_names():
    lov_payload = {
        "items": [
            {
                "tableName": "Disposition LOVs",
                "id": 38,
                "name": "Booked",
                "value": "Booked",
            },
            {
                "tableName": "Move_Type",
                "id": 119,
                "name": "Interstate",
                "value": "Interstate",
            },
        ],
        "count": 2,
    }
    lookup = build_lov_lookup(lov_payload)
    lead = {
        "dispositionId": 38,
        "dispositionName": None,
        "moveTypeId": 119,
        "moveTypeName": None,
    }
    resolved = resolve_lead_names(lead, lookup)
    assert resolved["dispositionName"] == "Booked"
    assert resolved["moveTypeName"] == "Interstate"


def test_build_lov_lookup_ignores_bad_cached_shape():
    assert build_lov_lookup({"items": {}, "count": 1}) == {}
