#!/usr/bin/env python3
"""Smoke-test GET /leads/{leadId}/inventory against a running middleware instance."""

import argparse
import json
import os
import sys

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="Test lead inventory endpoint")
    parser.add_argument("--base-url", default=os.environ.get("MSPAPI_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--api-key", default=os.environ.get("MSPAPI_KEY", ""))
    parser.add_argument("--lead-id", required=True)
    parser.add_argument("--estimate-id", default=None, help="Optional estimate override")
    parser.add_argument("--no-summary", action="store_true", help="Set includeSummary=false")
    args = parser.parse_args()

    if not args.api_key:
        print("Error: set --api-key or MSPAPI_KEY", file=sys.stderr)
        return 1

    params: dict[str, str] = {}
    if args.estimate_id:
        params["estimateId"] = args.estimate_id
    if args.no_summary:
        params["includeSummary"] = "false"

    url = f"{args.base_url.rstrip('/')}/leads/{args.lead_id}/inventory"
    headers = {"X-API-Key": args.api_key}

    with httpx.Client(timeout=120.0) as client:
        response = client.get(url, headers=headers, params=params)

    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2)[:8000])
        if isinstance(data, dict) and "rooms" in data:
            print(
                f"\nSummary: {len(data['rooms'])} rooms, "
                f"{data.get('grandTotals', {}).get('itemCount', 0)} items"
            )
    except json.JSONDecodeError:
        print(response.text[:2000])

    return 0 if response.is_success else 1


if __name__ == "__main__":
    raise SystemExit(main())
