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
    logic: str = "",
    sorting: str = "asc",
) -> dict[str, Any]:
    """Body for POST /api/services/app/Lead/GetAllLead (MoveScout SPA shape).

    Wire format captured in P11 (2026-09-22):
    - logic: "" for baseline (no filters), "and" when filters[] is non-empty
    - sorting: "asc" or "desc" (wire field; distinct from sort_dir)
    - sortDescriptor: {} (empty object in all captures)
    """
    effective_filters = filters or []
    effective_logic = logic if logic else ("and" if effective_filters else "")

    payload: dict[str, Any] = {
        "name": "",
        "logic": effective_logic,
        "bulkList": [],
        "filters": effective_filters,
        "sortDescriptor": {},
        "searchKeyWord": None,
        "defaultFilterLead": default_filter,
        "allSelectedLead": False,
        "leadsId": [],
        "loadVirtualSurveyCompleted": False,
        "dashboarNavigationLeads": False,
        "sorting": sorting,
        "maxResultCount": page_size,
        "skipCount": movescout_skip_count(page, page_size),
    }
    if sort_field:
        payload["sortField"] = sort_field
        payload["sortDir"] = sort_dir
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
    logic: str = "",
    sorting: str = "asc",
) -> Any:
    payload = build_get_all_lead_payload(
        default_filter=default_filter,
        filters=filters,
        page=page,
        page_size=page_size,
        sort_field=sort_field,
        sort_dir=sort_dir,
        logic=logic,
        sorting=sorting,
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
