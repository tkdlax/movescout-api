import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.api_key import generate_api_key, hash_api_key, verify_api_key
from app.main import app
from app.movescout.filters import build_filters, build_kendo_filter
from app.services.dedup import deduplicate_latest_per_lead
from app.services.lead_merge import deep_merge


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
