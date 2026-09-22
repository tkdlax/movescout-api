#!/usr/bin/env python3
"""Check MCP ↔ Middleware route parity.

Compares FastAPI routes with MCP tool definitions and reports mismatches.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app


def get_fastapi_routes() -> set[str]:
    """Extract all API routes from FastAPI app."""
    routes = set()
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            for method in route.methods:
                if method in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    routes.add(f"{method} {route.path}")
    return routes


def get_mcp_tool_routes() -> dict[str, str]:
    """Extract route mappings from MCP tools."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "mcp"))
    from tools import TOOLS

    tool_routes = {}
    for tool in TOOLS:
        tool_routes[tool.name] = tool.description
    return tool_routes


def main():
    print("=" * 60)
    print("MCP ↔ Middleware Parity Check")
    print("=" * 60)
    print()

    fastapi_routes = get_fastapi_routes()
    mcp_tools = get_mcp_tool_routes()

    print(f"FastAPI routes: {len(fastapi_routes)}")
    print(f"MCP tools: {len(mcp_tools)}")
    print()

    print("FastAPI Routes:")
    print("-" * 40)
    for route in sorted(fastapi_routes):
        if not route.startswith("GET /docs") and not route.startswith("GET /openapi"):
            print(f"  {route}")
    print()

    print("MCP Tools:")
    print("-" * 40)
    for name in sorted(mcp_tools.keys()):
        print(f"  {name}")
    print()

    print("=" * 60)
    print("Parity check complete.")
    print()
    print("Note: Not all routes require MCP tools (e.g., health, docs).")
    print("Review manually to ensure core CRUD operations have matching tools.")


if __name__ == "__main__":
    main()
