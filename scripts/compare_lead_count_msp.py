#!/usr/bin/env python3
"""Compare GetAllLead totalCount: direct MSP vs middleware (same filter)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx

from app.movescout.filters import build_kendo_filter
from app.movescout.headers import movescout_request_headers
from app.movescout.leads import get_all_leads


def _creation_filter(days: str) -> list[dict[str, Any]]:
    return [build_kendo_filter("creationTime", "eq", {"id": 8, "value": days})]


async def _msp_direct_count(
    *,
    username: str,
    password: str,
    base_url: str,
    default_filter: int,
    days: str,
    include_bad_sort: bool,
) -> tuple[int, dict[str, Any]]:
    auth_payload = {
        "userNameOrEmailAddress": username,
        "password": password,
        "rememberClient": True,
    }
    headers = movescout_request_headers()

    async with httpx.AsyncClient(base_url=base_url, timeout=120.0) as client:
        auth = await client.post(
            "/api/TokenAuth/Authenticate",
            json=auth_payload,
            headers=headers,
        )
        auth.raise_for_status()
        token = auth.json()["result"]["accessToken"]

        from app.movescout.client import MoveScoutClient

        async with MoveScoutClient(token) as ms_client:
            if include_bad_sort:
                # Old middleware shape that may reduce totalCount.
                payload = {
                    "defaultFilterLead": default_filter,
                    "filters": _creation_filter(days),
                    "skipCount": 0,
                    "maxResultCount": 500,
                    "sortField": "",
                    "sortDir": "desc",
                }
                response = await ms_client.request(
                    "POST", "/api/services/app/Lead/GetAllLead", json=payload
                )
                return int(response["result"]["totalCount"]), payload

            response = await get_all_leads(
                ms_client,
                default_filter=default_filter,
                filters=_creation_filter(days),
                page=1,
                page_size=500,
            )
            total = int(response["result"]["totalCount"])
            return total, {
                "name": "",
                "logic": "and",
                "bulkList": [],
                "filters": _creation_filter(days),
                "defaultFilterLead": default_filter,
                "maxResultCount": 500,
                "skipCount": 0,
            }


def _middleware_count(
    *,
    api_key: str,
    middleware_base: str,
    default_filter: int,
    days: str,
) -> int:
    filt = json.dumps(
        [{"field": "creationTime", "op": "eq", "value": {"id": 8, "value": days}}],
        separators=(",", ":"),
    )
    headers = {"X-API-Key": api_key}
    params = {"defaultFilter": default_filter, "maxResultSize": 500, "filter": filt}
    response = httpx.get(
        f"{middleware_base.rstrip('/')}/leads/page-count",
        headers=headers,
        params=params,
        timeout=120.0,
    )
    response.raise_for_status()
    return int(response.json()["totalCount"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare lead counts MSP direct vs middleware")
    parser.add_argument("--msp-username", default=os.environ.get("MSP_USERNAME", ""))
    parser.add_argument("--msp-password", default=os.environ.get("MSP_PASSWORD", ""))
    parser.add_argument(
        "--msp-base-url",
        default=os.environ.get("MOVESCOUT_BASE_URL", "https://movescoutproapi.sirva.com"),
    )
    parser.add_argument("--api-key", default=os.environ.get("MSPAPI_KEY", ""))
    parser.add_argument(
        "--middleware-base",
        default=os.environ.get("MSPAPI_BASE_URL", "https://mspapi.jbeckstead.com"),
    )
    parser.add_argument("--days", default="3")
    parser.add_argument("--default-filter", type=int, default=0)
    args = parser.parse_args()

    if not args.api_key:
        print("Error: set --api-key or MSPAPI_KEY", file=sys.stderr)
        return 1

    middleware_total = _middleware_count(
        api_key=args.api_key,
        middleware_base=args.middleware_base,
        default_filter=args.default_filter,
        days=args.days,
    )
    print(f"middleware totalCount={middleware_total}")

    if not args.msp_username or not args.msp_password:
        print("Skip direct MSP (set --msp-username/--msp-password to compare)", file=sys.stderr)
        return 0

    import asyncio

    async def run() -> None:
        good_total, _ = await _msp_direct_count(
            username=args.msp_username,
            password=args.msp_password,
            base_url=args.msp_base_url,
            default_filter=args.default_filter,
            days=args.days,
            include_bad_sort=False,
        )
        bad_total, bad_payload = await _msp_direct_count(
            username=args.msp_username,
            password=args.msp_password,
            base_url=args.msp_base_url,
            default_filter=args.default_filter,
            days=args.days,
            include_bad_sort=True,
        )
        print(f"MSP direct (UI-shaped payload) totalCount={good_total}")
        print(f"MSP direct (old middleware sortField/sortDir) totalCount={bad_total}")
        if bad_total != good_total:
            print("sortField='' sortDir='desc' changes totalCount on MSP")
            print(json.dumps(bad_payload, indent=2))

    asyncio.run(run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
