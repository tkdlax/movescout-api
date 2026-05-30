from datetime import UTC, datetime
from typing import Any

from app.movescout.client import MoveScoutClient
from app.movescout.paging import movescout_skip_count


async def get_all_estimates(
    client: MoveScoutClient,
    lead_id: str,
    *,
    page: int = 1,
    page_size: int = 15,
) -> Any:
    return await client.request(
        "POST",
        "/api/services/app/Inventory/GetAllEstimates",
        params={"leadId": lead_id},
        json={
            "name": "",
            "logic": "",
            "filters": [],
            "sortDescriptor": {},
            "isListForEstimate": True,
            "sorting": "asc",
            "maxResultCount": page_size,
            "skipCount": movescout_skip_count(page, page_size),
        },
    )


async def get_estimate_for_inventory_tab(client: MoveScoutClient, estimate_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/Inventory/GetEstimateByIdForInventoryTab",
        params={"estimateId": estimate_id},
    )


async def get_estimate_summary(client: MoveScoutClient, estimate_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/Inventory/GetEstimateSummary",
        params={"estimateId": estimate_id},
    )


async def get_booker_id_of_estimate(client: MoveScoutClient, estimate_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/Inventory/GetBookerIdOfEstimate",
        params={"Id": estimate_id},
    )


async def get_all_rooms_by_delta_for_estimate(
    client: MoveScoutClient,
    *,
    lead_id: str,
    estimate_id: str,
    date: str | None = None,
) -> Any:
    if date is None:
        date = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return await client.request(
        "GET",
        "/api/services/app/Inventory/GetAllRoomsByDeltaForEstimate",
        params={"date": date, "leadId": lead_id, "estimateId": estimate_id},
    )


def extract_estimate_list(response: Any) -> tuple[list[dict[str, Any]], int]:
    result = response.get("result", response) if isinstance(response, dict) else {}
    items = result.get("items") or result.get("data") or []
    total = result.get("totalCount") or result.get("total") or len(items)
    return items, int(total)
