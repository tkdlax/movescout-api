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


async def create_or_update_article_for_inventory(
    client: MoveScoutClient,
    article: dict[str, Any],
) -> Any:
    """Update a single inventory article in place (qty, weight, cube changes).
    
    This is distinct from CreateOrUpdateArticleForListInventory which takes an array.
    Use this for in-place edits on existing articles (e.g., qty bump, weight/cube change).
    
    Key fields (from P3-F packet evidence):
    - estimatesId: Estimate ID
    - articleId: Article catalog ID (required - identifies which article)
    - shippingQty: New shipping quantity
    - weight: Article weight
    - cube: Article cube (may be string or int)
    - isQtyChange: Set to true when editing quantity
    - roomId, segmentId: Location identifiers
    
    The response is the full Calculate result (not just success/fail).
    """
    return await client.request(
        "POST",
        "/api/services/app/Inventory/CreateOrUpdateArticleForInventory",
        json=article,
    )


async def create_or_update_segments(
    client: MoveScoutClient,
    segments_payload: dict[str, Any],
) -> Any:
    """Create or update segments for an estimate.
    
    P6 capture evidence: POST /api/services/app/Inventory/CreateOrUpdateSegments
    
    Request body shape:
    {
      "leadId": 1674404,
      "segmentDto": [
        {
          "estimatesId": "2395896",
          "pickupAddressId": 4860018,
          "deliveryAddressId": 4860019,
          "pickupAddressName": "[main pickup]",
          "deliveryAddressName": "[main delivery]",
          "cube": 53,
          "weight": 371,
          "modeId": 192,
          "name": "Segment 1",
          "tenantId": 1,
          "pickupStopName": "MainPickup",
          "deliveryStopName": "MainDelivery",
          "id": 2563983  // existing segment ID; use 0 for new
        }
      ],
      "id": 2395896  // estimate ID
    }
    
    Response: ABP envelope with new segment IDs.
    """
    return await client.request(
        "POST",
        "/api/services/app/Inventory/CreateOrUpdateSegments",
        json=segments_payload,
    )


async def save_extra_pickups_and_deliveries(
    client: MoveScoutClient,
    stops: list[dict[str, Any]],
) -> Any:
    """Save extra pickup and delivery stops for segments.
    
    P6 capture evidence: POST /api/services/app/Inventory/SaveExtraPickUpAndDeliveriesForSegments
    
    Request body is an array of stop address objects:
    [
      {
        "leadId": 1674404,
        "estimatesId": "2395896",
        "streetAddr1": "Will Advise",
        "streetAddr2": null,
        "zip": "80202",
        "city": "Denver",
        "state": "CO",
        "county": null,
        "country": "US",
        "contactFirstName": null,
        "contactNumber": null,
        "emailAddress": null,
        "addressType": 1,  // 1=pickup, 2=delivery
        "stopName": "XP1",
        "sequenceNumber": 2,
        "isMainPickup": false,
        "isMainDelivery": false,
        "id": 4862738  // address ID; 0 for new
      },
      // ... main stops also included
    ]
    
    Response: ABP envelope with assigned address IDs.
    """
    return await client.request(
        "POST",
        "/api/services/app/Inventory/SaveExtraPickUpAndDeliveriesForSegments",
        json=stops,
    )
