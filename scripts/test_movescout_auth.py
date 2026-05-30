#!/usr/bin/env python3
"""Test MoveScout login directly (bypasses API key / DB). Run inside the api container."""

import argparse
import json
import sys

import httpx

from app.config import get_settings

MOVESCOUT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
)


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Test MoveScout TokenAuth/Authenticate")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--base-url", default=settings.movescout_base_url)
    parser.add_argument("--origin", default=settings.movescout_origin)
    args = parser.parse_args()

    payload = {
        "userNameOrEmailAddress": args.username,
        "password": args.password,
        "rememberClient": True,
    }

    headers = {
        "Content-Type": "application/json-patch+json",
        "Accept": "text/plain",
        "Origin": args.origin,
        "Referer": f"{args.origin.rstrip('/')}/",
        "User-Agent": MOVESCOUT_USER_AGENT,
    }

    url = f"{args.base_url.rstrip('/')}/api/TokenAuth/Authenticate"
    print(f"POST {url}")
    print(f"User: {args.username}")
    print(f"Origin: {args.origin}")

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
    except httpx.HTTPError as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"HTTP {response.status_code}")
    print("--- Response body ---")
    try:
        data = response.json()
        print(json.dumps(data, indent=2)[:2000])
    except ValueError:
        print((response.text or "")[:2000])
        data = {}

    if response.status_code == 200:
        token = (data if isinstance(data, dict) else {}).get("result", {}).get("accessToken")
        if token:
            print("\nOK: accessToken received (login works)")
            sys.exit(0)
        print("\nFAIL: HTTP 200 but no accessToken — check success/error in JSON above", file=sys.stderr)
        sys.exit(1)

    print("\nFAIL: non-200 from MoveScout", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
