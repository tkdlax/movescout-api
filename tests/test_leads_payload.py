from unittest.mock import AsyncMock, MagicMock

import pytest

from app.movescout.filters import build_kendo_filter, prepare_lead_filters
from app.movescout.leads import build_get_all_lead_payload, get_all_leads


def test_prepare_lead_filters_passthrough_preserves_operator_and_value_types():
    raw = [
        {
            "field": "creationTime",
            "operator": "eq",
            "value": {"id": 8, "value": "3"},
            "condition": "and",
            "date": "Wed, 10 Jun 2026 06:00:00 GMT",
        }
    ]
    filters = prepare_lead_filters(raw)
    assert filters[0]["operator"] == "eq"
    assert filters[0]["value"] == {"id": 8, "value": "3"}
    assert filters[0]["date"] == "Wed, 10 Jun 2026 06:00:00 GMT"


def test_build_get_all_lead_payload_matches_movescout_spa():
    filters = [build_kendo_filter("creationTime", "eq", {"id": 8, "value": "3"})]
    payload = build_get_all_lead_payload(
        default_filter=0,
        filters=filters,
        page=1,
        page_size=500,
    )
    assert payload["name"] == ""
    assert payload["logic"] == "and"
    assert payload["bulkList"] == []
    assert payload["defaultFilterLead"] == 0
    assert payload["sortField"] == ""
    assert payload["sortDir"] == "desc"
    assert payload["maxResultCount"] == 500
    assert payload["skipCount"] == 0
    assert payload["filters"] == filters


def test_build_get_all_lead_payload_omits_logic_when_empty():
    payload = build_get_all_lead_payload(default_filter=0, logic="")
    assert "logic" not in payload


@pytest.mark.asyncio
async def test_get_all_leads_posts_spa_payload():
    client = MagicMock()
    client.request = AsyncMock(return_value={"result": {"items": [], "totalCount": 0}})

    filters = [build_kendo_filter("creationTime", "eq", {"id": 8, "value": "3"})]
    await get_all_leads(
        client,
        default_filter=0,
        filters=filters,
        page=1,
        page_size=500,
    )

    payload = client.request.await_args.kwargs["json"]
    assert payload["logic"] == "and"
    assert payload["sortField"] == ""
    assert payload["sortDir"] == "desc"
    assert "sortDescriptor" not in payload
