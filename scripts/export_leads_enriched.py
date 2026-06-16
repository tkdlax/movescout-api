#!/usr/bin/env python3
"""Export qualified leads enriched with primary-estimate pricing summary (Shape A CSV)."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import httpx

# Allow running from repo root without installing the package.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.reports.lead_export_filters import (  # noqa: E402
    build_creation_date_filters,
    filters_to_query_param,
    normalize_date_range,
)
from app.reports.lov_lookup import build_lov_lookup, resolve_lead_names  # noqa: E402
from app.reports.pricing_summary import (  # noqa: E402
    PRICING_META_COLUMNS,
    PRICING_SUB_FIELD_COLUMNS,
    CANONICAL_NET_FIELDS,
    discover_dynamic_net_columns,
    empty_pricing_summary,
    fill_dynamic_net_columns,
    pricing_summary_from_response,
    resolve_pricing_payload,
)
from app.services.csv_export import flatten_value  # noqa: E402

# Edit these, or set MSPAPI_KEY / MSPAPI_BASE_URL env vars, or pass CLI flags.
API_KEY = ""
BASE_URL = "https://mspapi.jbeckstead.com"
DEFAULT_FILTER = 3


def _lead_id(lead: dict[str, Any]) -> str | None:
    value = lead.get("id") or lead.get("leadId")
    return str(value) if value is not None else None


def _slug_for_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-").lower() or "range"


def fetch_lov(
    client: httpx.Client,
    *,
    base_url: str,
    api_key: str,
) -> dict[str, dict[Any, str]]:
    headers = {"X-API-Key": api_key}
    response = client.get(f"{base_url.rstrip('/')}/lov", headers=headers)
    response.raise_for_status()
    return build_lov_lookup(response.json())


def fetch_leads(
    client: httpx.Client,
    *,
    base_url: str,
    api_key: str,
    filter_param: str,
    default_filter: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    headers = {"X-API-Key": api_key}
    root = base_url.rstrip("/")
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
            leads.extend(item for item in items if isinstance(item, dict))
        print(f"Fetched leads page {page}/{page_count} ({len(leads)} rows)", file=sys.stderr)

    return leads, total_count


def _request_with_retries(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    retries: int,
) -> httpx.Response:
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = client.request(method, url, headers=headers)
            if response.status_code in {502, 503, 504} and attempt < retries:
                time.sleep(min(2**attempt, 8))
                continue
            return response
        except httpx.HTTPError as exc:
            last_exc = exc
            if attempt >= retries:
                raise
            time.sleep(min(2**attempt, 8))
    raise last_exc or RuntimeError("request failed")


def fetch_pricing_for_lead(
    client: httpx.Client,
    *,
    base_url: str,
    api_key: str,
    lead_id: str,
    retries: int,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    headers = {"X-API-Key": api_key}
    url = f"{base_url.rstrip('/')}/leads/{lead_id}/pricing"
    response = _request_with_retries(client, "GET", url, headers=headers, retries=retries)

    if response.status_code == 404:
        return empty_pricing_summary(has_primary_estimate=False), None

    if not response.is_success:
        detail = response.text[:300]
        return (
            empty_pricing_summary(
                has_primary_estimate=False,
                pricing_fetch_error=f"HTTP {response.status_code}: {detail}",
            ),
            None,
        )

    data = response.json()
    if not isinstance(data, dict):
        return (
            empty_pricing_summary(
                has_primary_estimate=False,
                pricing_fetch_error="Invalid pricing response (not an object)",
            ),
            None,
        )

    return pricing_summary_from_response(data), resolve_pricing_payload(data)


def enrich_leads_with_pricing(
    client: httpx.Client,
    *,
    base_url: str,
    api_key: str,
    leads: list[dict[str, Any]],
    concurrency: int,
    retries: int,
) -> tuple[list[dict[str, Any]], list[str], int]:
    indexed: list[tuple[int, str, dict[str, Any]]] = []
    for index, lead in enumerate(leads):
        lead_id = _lead_id(lead)
        if lead_id is None:
            continue
        indexed.append((index, lead_id, lead))

    pricing_by_index: dict[int, dict[str, Any]] = {}
    raw_pricing_by_index: dict[int, dict[str, Any]] = {}
    errors = 0
    completed = 0
    total = len(indexed)

    def _task(item: tuple[int, str, dict[str, Any]]) -> tuple[int, dict[str, Any], dict[str, Any] | None]:
        index, lead_id, _lead = item
        summary, raw_pricing = fetch_pricing_for_lead(
            client,
            base_url=base_url,
            api_key=api_key,
            lead_id=lead_id,
            retries=retries,
        )
        return index, summary, raw_pricing

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        futures = [pool.submit(_task, item) for item in indexed]
        for future in as_completed(futures):
            index, summary, raw_pricing = future.result()
            pricing_by_index[index] = summary
            if raw_pricing is not None:
                raw_pricing_by_index[index] = raw_pricing
            if summary.get("pricingFetchError"):
                errors += 1
            completed += 1
            if completed % 50 == 0 or completed == total:
                print(
                    f"Pricing {completed}/{total} (errors: {errors})",
                    file=sys.stderr,
                )

    raw_pricing_payloads = list(raw_pricing_by_index.values())
    dynamic_columns = discover_dynamic_net_columns(raw_pricing_payloads)

    enriched: list[dict[str, Any]] = []
    for index, lead in enumerate(leads):
        pricing = pricing_by_index.get(index)
        if pricing is None:
            pricing = empty_pricing_summary(has_primary_estimate=False)
        else:
            pricing = dict(pricing)
            if pricing.get("hasPrimaryEstimate"):
                raw = raw_pricing_by_index.get(index, {})
                pricing = fill_dynamic_net_columns(pricing, raw, dynamic_columns)
        enriched.append({**lead, **pricing})

    return enriched, dynamic_columns, errors


def _pricing_column_order(dynamic_columns: list[str]) -> list[str]:
    canonical = list(CANONICAL_NET_FIELDS.keys())
    dynamic_only = [column for column in dynamic_columns if column not in canonical]
    return [
        *PRICING_META_COLUMNS,
        *canonical,
        *dynamic_only,
        *PRICING_SUB_FIELD_COLUMNS,
    ]


def build_csv_rows(
    leads: list[dict[str, Any]],
    *,
    lov_lookup: dict[str, dict[Any, str]] | None,
    pricing_column_order: list[str],
) -> tuple[list[str], list[dict[str, Any]]]:
    resolved_leads = [resolve_lead_names(lead, lov_lookup) for lead in leads]
    lead_fieldnames = sorted({key for lead in resolved_leads for key in lead.keys()})
    fieldnames = lead_fieldnames + [col for col in pricing_column_order if col not in lead_fieldnames]

    rows: list[dict[str, Any]] = []
    for lead in resolved_leads:
        row = {field: lead.get(field) for field in fieldnames}
        rows.append(row)
    return fieldnames, rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: flatten_value(row.get(key)) for key in fieldnames})


def discover_pricing_columns(
    dynamic_columns: list[str],
) -> list[str]:
    return _pricing_column_order(dynamic_columns)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export leads with primary-estimate pricing summary as a wide CSV"
    )
    parser.add_argument("--base-url", default=os.environ.get("MSPAPI_BASE_URL", BASE_URL))
    parser.add_argument("--api-key", default=os.environ.get("MSPAPI_KEY", API_KEY))
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD or 'Jan 1, 2026')")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD or 'Jan 1, 2026')")
    parser.add_argument(
        "--default-filter",
        type=int,
        default=DEFAULT_FILTER,
        help="MoveScout defaultFilterLead (default: 3 qualified)",
    )
    parser.add_argument("--page-size", type=int, default=500, help="Leads per page (max 1000)")
    parser.add_argument("--concurrency", type=int, default=8, help="Parallel pricing requests")
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP read timeout seconds")
    parser.add_argument("--retries", type=int, default=3, help="Retries on 502/503/timeout")
    parser.add_argument("--output", default=None, help="Output CSV path")
    args = parser.parse_args()

    if not args.api_key:
        print("Error: set API_KEY in script, MSPAPI_KEY env var, or --api-key", file=sys.stderr)
        return 1

    try:
        start_fmt, end_fmt = normalize_date_range(args.start, args.end)
        filters = build_creation_date_filters(args.start, args.end)
        filter_param = filters_to_query_param(filters)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(
            f"leads_enriched_{_slug_for_filename(start_fmt)}_{_slug_for_filename(end_fmt)}.csv"
        )

    page_size = min(max(args.page_size, 1), 1000)
    started = time.perf_counter()

    try:
        with httpx.Client(timeout=args.timeout) as client:
            lov_lookup: dict[str, dict[Any, str]] | None
            try:
                lov_lookup = fetch_lov(client, base_url=args.base_url, api_key=args.api_key)
                print(f"Loaded LOV lookup ({len(lov_lookup)} list types)", file=sys.stderr)
            except httpx.HTTPError as exc:
                lov_lookup = None
                print(f"Warning: LOV fetch failed ({exc}); exporting IDs only", file=sys.stderr)

            leads, total_count = fetch_leads(
                client,
                base_url=args.base_url,
                api_key=args.api_key,
                filter_param=filter_param,
                default_filter=args.default_filter,
                page_size=page_size,
            )
            print(f"Total leads from API: {total_count}", file=sys.stderr)

            enriched, dynamic_columns, pricing_errors = enrich_leads_with_pricing(
                client,
                base_url=args.base_url,
                api_key=args.api_key,
                leads=leads,
                concurrency=args.concurrency,
                retries=args.retries,
            )

            pricing_columns = discover_pricing_columns(dynamic_columns)
            fieldnames, rows = build_csv_rows(
                enriched,
                lov_lookup=lov_lookup,
                pricing_column_order=pricing_columns,
            )
            write_csv(output_path, fieldnames, rows)
    except httpx.HTTPStatusError as exc:
        print(f"HTTP {exc.response.status_code}: {exc.response.text[:500]}", file=sys.stderr)
        return 1
    except httpx.HTTPError as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    elapsed = time.perf_counter() - started
    with_estimate = sum(1 for row in rows if row.get("hasPrimaryEstimate") is True)
    print(
        json.dumps(
            {
                "output": str(output_path),
                "totalCount": total_count,
                "rowsWritten": len(rows),
                "withPrimaryEstimate": with_estimate,
                "pricingErrors": pricing_errors,
                "elapsedSeconds": round(elapsed, 1),
                "dateRange": {"start": start_fmt, "end": end_fmt},
            },
            indent=2,
        ),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
