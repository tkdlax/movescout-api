"""Tests for MoveScout LOV client and lookup."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.movescout.lov import get_all_list_of_values
from app.reports.lov_lookup import build_lov_lookup


@pytest.mark.asyncio
async def test_get_all_list_of_values_uses_get():
    client = MagicMock()
    client.request = AsyncMock(return_value={"result": {"items": []}})
    await get_all_list_of_values(client)
    client.request.assert_awaited_once_with(
        "GET",
        "/api/services/app/ListOfValue/GetAllListofvalues",
    )


def test_build_lov_lookup_maps_movescout_table_names():
    lookup = build_lov_lookup(
        {
            "items": [
                {"tableName": "Disposition LOVs", "id": 43, "name": "New"},
                {"tableName": "Move_Type", "id": 119, "name": "Interstate"},
                {"tableName": "SHIPPER_TYPE", "id": 145, "name": "Consumer"},
            ]
        }
    )
    assert lookup["disposition"][43] == "New"
    assert lookup["moveType"][119] == "Interstate"
    assert lookup["shipperType"][145] == "Consumer"
