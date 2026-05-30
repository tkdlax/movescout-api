from typing import Any

from app.movescout.client import MoveScoutClient
from app.movescout.leads import extract_lead_list, get_all_leads
from app.movescout.paging import MOVESCOUT_PROBE_MAX_RESULT, movescout_page_count


async def probe_leads_total_count(
    client: MoveScoutClient,
    *,
    default_filter: int = 3,
    filters: list[dict[str, Any]] | None = None,
    sort_field: str | None = None,
    sort_dir: str = "desc",
) -> int:
    """One MoveScout call: skipCount=0, maxResultCount=1 → totalCount."""
    probe = await get_all_leads(
        client,
        default_filter=default_filter,
        filters=filters,
        page=1,
        page_size=MOVESCOUT_PROBE_MAX_RESULT,
        sort_field=sort_field,
        sort_dir=sort_dir,
    )
    _, total = extract_lead_list(probe)
    return total


async def leads_page_count_response(
    client: MoveScoutClient,
    *,
    default_filter: int = 3,
    filters: list[dict[str, Any]] | None = None,
    max_result_size: int = 500,
    sort_field: str | None = None,
    sort_dir: str = "desc",
) -> dict[str, Any]:
    total = await probe_leads_total_count(
        client,
        default_filter=default_filter,
        filters=filters,
        sort_field=sort_field,
        sort_dir=sort_dir,
    )
    return {
        "totalCount": total,
        "pageCount": movescout_page_count(total, max_result_size),
        "maxResultSize": max_result_size,
    }


async def list_leads_page_response(
    client: MoveScoutClient,
    *,
    default_filter: int = 3,
    filters: list[dict[str, Any]] | None = None,
    page: int = 1,
    max_result_size: int = 500,
    sort_field: str | None = None,
    sort_dir: str = "desc",
) -> dict[str, Any]:
    """Fetch a single page; caller drives pagination using page-count first."""
    response = await get_all_leads(
        client,
        default_filter=default_filter,
        filters=filters,
        page=page,
        page_size=max_result_size,
        sort_field=sort_field,
        sort_dir=sort_dir,
    )
    items, total = extract_lead_list(response)
    return {
        "items": items,
        "totalCount": total,
        "pageCount": movescout_page_count(total, max_result_size),
        "page": page,
        "maxResultSize": max_result_size,
    }


async def fetch_all_leads_paginated(
    client: MoveScoutClient,
    *,
    default_filter: int = 3,
    filters: list[dict[str, Any]] | None = None,
    page_size: int = 500,
    sort_field: str | None = None,
    sort_dir: str = "desc",
) -> tuple[list[dict[str, Any]], int]:
    """Fetch every page (CSV export only — loads full result set in memory)."""
    total = await probe_leads_total_count(
        client,
        default_filter=default_filter,
        filters=filters,
        sort_field=sort_field,
        sort_dir=sort_dir,
    )
    if total <= 0:
        return [], 0

    num_pages = movescout_page_count(total, page_size)
    all_items: list[dict[str, Any]] = []

    for page in range(1, num_pages + 1):
        response = await get_all_leads(
            client,
            default_filter=default_filter,
            filters=filters,
            page=page,
            page_size=page_size,
            sort_field=sort_field,
            sort_dir=sort_dir,
        )
        items, _ = extract_lead_list(response)
        all_items.extend(items)

    return all_items, total


async def fetch_all_activities_paginated(
    client: MoveScoutClient,
    *,
    lead_id: str | None = None,
    filters: list[dict[str, Any]] | None = None,
    page_size: int = 500,
) -> tuple[list[dict[str, Any]], int]:
    from app.movescout.activities import extract_activity_list, get_activities

    probe = await get_activities(
        client,
        lead_id=lead_id,
        filters=filters,
        page=1,
        page_size=MOVESCOUT_PROBE_MAX_RESULT,
    )
    _, total = extract_activity_list(probe)
    if total <= 0:
        return [], 0

    num_pages = movescout_page_count(total, page_size)
    all_items: list[dict[str, Any]] = []

    for page in range(1, num_pages + 1):
        response = await get_activities(
            client,
            lead_id=lead_id,
            filters=filters,
            page=page,
            page_size=page_size,
        )
        items, _ = extract_activity_list(response)
        all_items.extend(items)

    return all_items, total
