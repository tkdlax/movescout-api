import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.api_key import generate_api_key, hash_api_key, verify_api_key
from app.main import app
from app.movescout.filters import build_filters, build_kendo_filter
from app.movescout.paging import movescout_page_count, movescout_skip_count
from app.routes.lov import _normalize_lov_result
from app.services.dedup import deduplicate_latest_per_lead
from app.services.inventory_transform import build_inventory_response, group_survey_by_room
from app.services.lead_merge import deep_merge
from app.services.reference_cache import clear_cache as clear_reference_cache
from app.services.reference_cache import get_or_load as ref_get_or_load


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_protected_route_requires_api_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/leads")
    assert response.status_code == 422


def test_api_key_hash_and_verify():
    key = generate_api_key()
    hashed = hash_api_key(key)
    assert verify_api_key(key, hashed)
    assert not verify_api_key("wrong-key", hashed)


def test_movescout_skip_count():
    assert movescout_skip_count(1, 100) == 0
    assert movescout_skip_count(2, 100) == 100
    assert movescout_skip_count(3, 50) == 100


@pytest.mark.asyncio
async def test_lov_cache_reuses_loader():
    clear_reference_cache()
    calls = 0

    async def loader() -> dict[str, str]:
        nonlocal calls
        calls += 1
        return {"n": calls}

    from uuid import uuid4

    user_id = uuid4()
    first = await ref_get_or_load(user_id, "lov", loader)
    second = await ref_get_or_load(user_id, "lov", loader)
    assert first == {"n": 1}
    assert second == {"n": 1}
    assert calls == 1
    clear_reference_cache(user_id, "lov")


@pytest.mark.asyncio
async def test_reference_cache_namespace_isolation():
    clear_reference_cache()
    from uuid import uuid4

    user_id = uuid4()

    async def loader_a() -> str:
        return "a"

    async def loader_b() -> str:
        return "b"

    assert await ref_get_or_load(user_id, "ns_a", loader_a) == "a"
    assert await ref_get_or_load(user_id, "ns_b", loader_b) == "b"
    clear_reference_cache()


def test_group_survey_by_room():
    survey = [
        {
            "id": 1,
            "roomId": 37,
            "roomName": "Living Room",
            "articleName": "Sofa",
            "shippingQty": 1,
            "weight": 350,
            "cube": 50,
            "shippingTotal": 350,
        },
        {
            "id": 2,
            "roomId": 37,
            "roomName": "Living Room",
            "articleName": "Chair",
            "shippingQty": 2,
            "weight": 84,
            "cube": 12,
            "shippingTotal": 168,
        },
        {
            "id": 3,
            "roomId": 39,
            "roomName": "Master Bedroom",
            "articleName": "Bed",
            "shippingQty": 1,
            "weight": 35,
            "cube": 5,
            "shippingTotal": 35,
        },
    ]
    summaries = [
        {
            "roomId": 37,
            "roomName": "Living Room",
            "sumShippingQuantity": 3,
            "sumWeight": 434.0,
            "sumCube": 62.0,
            "sumShippingTotal": 518.0,
        }
    ]
    rooms, warnings, grand = group_survey_by_room(survey, room_summaries=summaries)
    assert len(rooms) == 2
    assert grand["itemCount"] == 3
    assert grand["shippingQty"] == 4
    living = next(r for r in rooms if r["roomId"] == 37)
    assert living["itemCount"] == 2
    assert living["totals"]["weight"] == 434.0
    assert not warnings


def test_group_survey_shipping_only():
    survey = [
        {"roomId": 1, "roomName": "Kitchen", "shippingQty": 0, "weight": 350, "cube": 50},
        {"roomId": 1, "roomName": "Kitchen", "shippingQty": 1, "weight": 10, "cube": 2},
    ]
    rooms, _, grand = group_survey_by_room(survey, shipping_only=True)
    assert grand["itemCount"] == 1
    assert rooms[0]["items"][0]["weight"] == 10


def test_build_inventory_response_empty_survey():
    result = build_inventory_response(
        lead_id="1553516",
        estimate_dto={"id": 2192413, "estimateName": "Test", "leadSurveyDto": []},
        primary_meta={"estimateId": 2192413},
    )
    assert result["rooms"] == []
    assert result["grandTotals"]["itemCount"] == 0
    assert result["isEstimateWithInventory"] is False


def test_normalize_lov_result_list():
    out = _normalize_lov_result([{"id": 1}, {"id": 2}])
    assert out["count"] == 2
    assert len(out["items"]) == 2


def test_normalize_lov_result_empty_dict():
    out = _normalize_lov_result({})
    assert out == {"items": [], "count": 0}


def test_normalize_lov_result_paged_upstream():
    out = _normalize_lov_result(
        {
            "totalCount": 2,
            "items": [
                {"tableName": "Move_Type", "id": 119, "name": "Interstate"},
            ],
        }
    )
    assert out["count"] == 2
    assert len(out["items"]) == 1


def test_movescout_page_count():
    assert movescout_page_count(0, 500) == 0
    assert movescout_page_count(1, 500) == 1
    assert movescout_page_count(500, 500) == 1
    assert movescout_page_count(501, 500) == 2
    assert movescout_page_count(1500, 500) == 3


def test_build_kendo_filter():
    result = build_kendo_filter("salesRepName", "contains", "Jacob")
    assert result["field"] == "salesRepName"
    assert result["operator"] == "contains"
    assert result["value"] == "Jacob"
    assert "date" in result


def test_build_filters_rejects_unknown_field():
    with pytest.raises(ValueError, match="not allowed"):
        build_filters([{"field": "unknownField", "op": "eq", "value": 1}])


def test_deep_merge():
    base = {"a": 1, "nested": {"x": 1, "y": 2}}
    updates = {"b": 2, "nested": {"y": 3, "z": 4}}
    merged = deep_merge(base, updates)
    assert merged == {"a": 1, "b": 2, "nested": {"x": 1, "y": 3, "z": 4}}


def test_deduplicate_latest_per_lead():
    activities = [
        {"leadId": "1", "activityStart": "2026-01-01T10:00:00"},
        {"leadId": "1", "activityStart": "2026-02-01T10:00:00"},
        {"leadId": "2", "activityStart": "2026-01-15T10:00:00"},
    ]
    result = deduplicate_latest_per_lead(activities)
    assert len(result) == 2
    by_lead = {a["leadId"]: a for a in result}
    assert by_lead["1"]["activityStart"] == "2026-02-01T10:00:00"
