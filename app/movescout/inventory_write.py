from typing import Any

from app.movescout.client import MoveScoutClient


async def create_or_update_estimates(
    client: MoveScoutClient,
    estimate: dict[str, Any],
) -> Any:
    """Create or update an estimate (with or without inventory flag)."""
    return await client.request(
        "POST",
        "/api/services/app/Inventory/CreateOrUpdateEstimates",
        json=estimate,
    )


async def create_or_update_room(
    client: MoveScoutClient,
    room: dict[str, Any],
) -> Any:
    """Create or update a room for an estimate."""
    return await client.request(
        "POST",
        "/api/services/app/Inventory/CreateOrUpdateRoom",
        json=room,
    )


async def create_article_from_inventory(
    client: MoveScoutClient,
    article: dict[str, Any],
) -> Any:
    """Create a custom article for a room."""
    return await client.request(
        "POST",
        "/api/services/app/Inventory/CreateArticleFromInventory",
        json=article,
    )


async def create_or_update_article_for_list_inventory(
    client: MoveScoutClient,
    inventory_lines: list[dict[str, Any]],
) -> Any:
    """Update inventory line items (quantities, weights, etc.)."""
    return await client.request(
        "POST",
        "/api/services/app/Inventory/CreateOrUpdateArticleForListInventory",
        json=inventory_lines,
    )


async def save_estimate_with_true_flag(
    client: MoveScoutClient,
    *,
    estimate_id: str,
    lead_id: str,
    density: int = 7,
) -> Any:
    """Commit/save inventory changes for an estimate."""
    return await client.request(
        "POST",
        "/api/services/app/InventoryCommon/SaveEstimateWithTrueFlag",
        params={
            "estimateId": estimate_id,
            "leadId": lead_id,
            "density": density,
        },
        json=None,
    )


async def get_all_articles_group_by_room(
    client: MoveScoutClient,
    *,
    lead_id: str,
    estimate_id: str,
    room_id: int,
) -> Any:
    """Get article catalog for a specific room (standard library articles)."""
    return await client.request(
        "GET",
        "/api/services/app/Inventory/GetAllArticlesGroupByRoomSP",
        params={
            "leadId": lead_id,
            "estimateId": estimate_id,
            "roomId": room_id,
        },
    )
