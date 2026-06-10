from typing import Any

from app.movescout.client import MoveScoutClient
from app.movescout.paging import movescout_skip_count


def build_get_all_lead_payload(
    *,
    default_filter: int = 3,
    filters: list[dict[str, Any]] | None = None,
    page: int = 1,
    page_size: int = 100,
    sort_field: str | None = None,
    sort_dir: str = "desc",
    logic: str = "and",
) -> dict[str, Any]:
    """Body for POST /api/services/app/Lead/GetAllLead (MoveScout SPA shape)."""
    payload: dict[str, Any] = {
        "name": "",
        "bulkList": [],
        "filters": filters or [],
        "sortField": sort_field or "",
        "sortDir": sort_dir,
        "defaultFilterLead": default_filter,
        "maxResultCount": page_size,
        "skipCount": movescout_skip_count(page, page_size),
    }
    if logic:
        payload["logic"] = logic
    return payload


async def get_all_leads(
    client: MoveScoutClient,
    *,
    default_filter: int = 3,
    filters: list[dict[str, Any]] | None = None,
    page: int = 1,
    page_size: int = 100,
    sort_field: str | None = None,
    sort_dir: str = "desc",
    logic: str = "and",
) -> Any:
    payload = build_get_all_lead_payload(
        default_filter=default_filter,
        filters=filters,
        page=page,
        page_size=page_size,
        sort_field=sort_field,
        sort_dir=sort_dir,
        logic=logic,
    )
    return await client.request("POST", "/api/services/app/Lead/GetAllLead", json=payload)


async def get_lead_by_id(client: MoveScoutClient, lead_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/Lead/GetLeadById",
        params={"leadId": lead_id},
    )


async def create_or_update_lead(client: MoveScoutClient, lead: dict[str, Any]) -> Any:
    return await client.request(
        "POST",
        "/api/services/app/Lead/CreateOrUpdateLead",
        json=lead,
    )


async def update_lead_from_appointment(client: MoveScoutClient, lead: dict[str, Any]) -> Any:
    return await client.request(
        "PUT",
        "/api/services/app/Lead/UpdateLeadFromAppointment",
        json=lead,
    )


def extract_lead_list(response: Any) -> tuple[list[dict[str, Any]], int]:
    result = response.get("result", response) if isinstance(response, dict) else {}
    items = result.get("items") or result.get("data") or []
    total = result.get("totalCount") or result.get("total") or len(items)
    return items, int(total)


def extract_single_lead(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        return response.get("result", response)
    return {}
