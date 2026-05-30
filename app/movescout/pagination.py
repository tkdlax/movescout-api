from typing import Any

from app.movescout.client import MoveScoutClient
from app.movescout.leads import extract_lead_list, get_all_leads


async def fetch_all_leads_paginated(
    client: MoveScoutClient,
    *,
    default_filter: int = 3,
    filters: list[dict[str, Any]] | None = None,
    page_size: int = 500,
    sort_field: str | None = None,
    sort_dir: str = "desc",
) -> list[dict[str, Any]]:
    all_items: list[dict[str, Any]] = []
    page = 1

    while True:
        response = await get_all_leads(
            client,
            default_filter=default_filter,
            filters=filters,
            page=page,
            page_size=page_size,
            sort_field=sort_field,
            sort_dir=sort_dir,
        )
        items, total = extract_lead_list(response)
        all_items.extend(items)

        if len(all_items) >= total or not items:
            break
        page += 1

    return all_items
