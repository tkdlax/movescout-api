#!/usr/bin/env python3
"""List lead IDs created in the last N days via the MoveScout middleware API."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx

# Edit these, or set MSPAPI_KEY / MSPAPI_BASE_URL env vars, or pass CLI flags.
API_KEY = ""
BASE_URL = "https://mspapi.jbeckstead.com"
DEFAULT_DAYS = 3
DEFAULT_FILTER = 0  # 0 = all leads; 3 = qualified leads only (MoveScout defaultFilterLead)


def _lead_id(lead: dict[str, Any]) -> str | None:
    value = lead.get("id") or lead.get("leadId")
    return str(value) if value is not None else None


def _build_creation_filter(days: int) -> str:
    """MoveScout relative creationTime filter (UI uses id=8, value as string)."""
    filters = [
        {
            "field": "creationTime",
            "op": "eq",
            "value": {"id": 8, "value": str(days)},
        }
    ]
    return json.dumps(filters, separators=(",", ":"))


def fetch_recent_leads(
    client: httpx.Client,
    *,
    base_url: str,
    api_key: str,
    days: int,
    page_size: int,
    default_filter: int,
) -> tuple[list[dict[str, Any]], int]:
    headers = {"X-API-Key": api_key}
    root = base_url.rstrip("/")
    filter_param = _build_creation_filter(days)
    common_params = {
        "filter": filter_param,
        "defaultFilter": default_filter,
        "maxResultSize": page_size,
        "sortField": "creationTime",
        "sortDir": "desc",
    }

    count_response = client.get(f"{root}/leads/page-count", headers=headers, params=common_params)
    count_response.raise_for_status()
    page_count = int(count_response.json().get("pageCount") or 0)
    total_count = int(count_response.json().get("totalCount") or 0)

    if page_count == 0:
        return [], total_count

    leads: list[dict[str, Any]] = []
    for page in range(1, page_count + 1):
        page_response = client.get(
            f"{root}/leads",
            headers=headers,
            params={**common_params, "page": page},
        )
        page_response.raise_for_status()
        items = page_response.json().get("items") or []
        if isinstance(items, list):
            leads.extend(items)

    return leads, total_count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch lead IDs from the last N days using GET /leads on the middleware API"
    )
    parser.add_argument("--base-url", default=os.environ.get("MSPAPI_BASE_URL", BASE_URL))
    parser.add_argument("--api-key", default=os.environ.get("MSPAPI_KEY", API_KEY))
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help="Last N days (default: 3)")
    parser.add_argument(
        "--page-size",
        type=int,
        default=500,
        help="Leads per page (max 1000)",
    )
    parser.add_argument(
        "--default-filter",
        type=int,
        default=DEFAULT_FILTER,
        help="MoveScout defaultFilterLead (UI lead list uses 0)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON array of {leadId, creationTime, firstName, lastName} instead of IDs only",
    )
    args = parser.parse_args()

    if not args.api_key:
        print("Error: set API_KEY in this file, MSPAPI_KEY env var, or --api-key", file=sys.stderr)
        return 1

    if args.days < 1:
        print("Error: --days must be at least 1", file=sys.stderr)
        return 1

    try:
        with httpx.Client(timeout=120.0) as client:
            leads, total_count = fetch_recent_leads(
                client,
                base_url=args.base_url,
                api_key=args.api_key,
                days=args.days,
                page_size=min(args.page_size, 1000),
                default_filter=args.default_filter,
            )
    except httpx.HTTPStatusError as exc:
        print(f"HTTP {exc.response.status_code}: {exc.response.text[:500]}", file=sys.stderr)
        return 1
    except httpx.HTTPError as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        rows = []
        for lead in leads:
            lead_id = _lead_id(lead)
            if lead_id is None:
                continue
            rows.append(
                {
                    "leadId": lead_id,
                    "creationTime": lead.get("creationTime"),
                    "firstName": lead.get("firstName"),
                    "lastName": lead.get("lastName"),
                    "disposition": lead.get("disposition"),
                }
            )
        print(json.dumps({"totalCount": total_count, "returned": len(rows), "leads": rows}, indent=2))
        return 0

    seen: set[str] = set()
    for lead in leads:
        lead_id = _lead_id(lead)
        if lead_id and lead_id not in seen:
            seen.add(lead_id)
            print(lead_id)

    print(f"# {len(seen)} lead(s) (totalCount={total_count})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
