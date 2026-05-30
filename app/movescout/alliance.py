from typing import Any

from app.movescout.client import MoveScoutClient


async def list_service_item_categories(client: MoveScoutClient) -> Any:
    return await client.request(
        "POST",
        "/api/services/app/Alliance/ListServiceItemCategories",
        json={},
    )


async def list_service_items_types(client: MoveScoutClient) -> Any:
    return await client.request(
        "POST",
        "/api/services/app/Alliance/ListServiceItemsTypes",
        json={},
    )


async def list_service_items(client: MoveScoutClient) -> Any:
    return await client.request(
        "POST",
        "/api/services/app/Alliance/ListServiceItems",
        json={},
    )


async def get_alliance_by_lead_estimate_id(client: MoveScoutClient, estimate_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/Alliance/GetAllianceByLeadEstimateId",
        params={"Id": estimate_id},
    )


async def list_price_classes(client: MoveScoutClient, booker_id: str) -> Any:
    return await client.request(
        "POST",
        "/api/services/app/Alliance/ListPriceClasses",
        params={"input": booker_id},
        json={},
    )
