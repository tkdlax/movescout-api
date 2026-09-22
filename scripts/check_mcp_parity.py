#!/usr/bin/env python3
"""Check MCP ↔ Middleware route parity.

Compares MCP tool definitions with expected middleware routes.
Does not require database dependencies.
"""

import re
import sys
from pathlib import Path


def get_route_files() -> list[Path]:
    """Get all route files from the app/routes directory."""
    routes_dir = Path(__file__).parent.parent / "app" / "routes"
    return list(routes_dir.glob("*.py"))


def extract_routes_from_file(filepath: Path) -> set[str]:
    """Extract route definitions from a Python file using regex."""
    routes = set()
    content = filepath.read_text()
    
    # Match @router.get("/path"), @router.post("/path"), etc.
    pattern = r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
    for match in re.finditer(pattern, content, re.IGNORECASE):
        method = match.group(1).upper()
        path = match.group(2)
        routes.add(f"{method} {path}")
    
    return routes


def get_fastapi_routes() -> set[str]:
    """Extract all API routes from route files."""
    routes = set()
    for route_file in get_route_files():
        if route_file.name != "__init__.py":
            routes.update(extract_routes_from_file(route_file))
    return routes


def get_mcp_tools() -> list[tuple[str, str]]:
    """Extract MCP tool names and descriptions."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "mcp"))
    from tools import TOOLS

    return [(tool.name, tool.description[:80] + "..." if len(tool.description) > 80 else tool.description) for tool in TOOLS]


def main():
    print("=" * 60)
    print("MCP ↔ Middleware Parity Check")
    print("=" * 60)
    print()

    fastapi_routes = get_fastapi_routes()
    mcp_tools = get_mcp_tools()

    print(f"Middleware routes: {len(fastapi_routes)}")
    print(f"MCP tools: {len(mcp_tools)}")
    print()

    print("Middleware Routes (from app/routes/*.py):")
    print("-" * 40)
    for route in sorted(fastapi_routes):
        print(f"  {route}")
    print()

    print("MCP Tools:")
    print("-" * 40)
    for name, desc in sorted(mcp_tools):
        print(f"  {name}")
    print()

    # Expected parity mapping
    expected_tools = {
        "movescout_leads_list": "GET /leads",
        "movescout_leads_get": "GET /leads/{lead_id}",
        "movescout_leads_create": "POST /leads",
        "movescout_leads_update": "PUT /leads/{lead_id}",
        "movescout_leads_move_type": "GET /leads/move-type",
        "movescout_activities_list": "GET /leads/{lead_id}/appointments",
        "movescout_activities_get": "GET /activities/{activity_id}",
        "movescout_activities_create": "POST /leads/{lead_id}/activities",
        "movescout_estimates_list": "GET /leads/{lead_id}/estimates",
        "movescout_estimates_get_primary": "GET /leads/{lead_id}/estimates/primary",
        "movescout_estimates_get": "GET /leads/{lead_id}/estimates/{estimate_id}",
        "movescout_estimates_create": "POST /leads/{lead_id}/estimates",
        "movescout_estimates_update": "PUT /leads/{lead_id}/estimates/{estimate_id}",
        "movescout_estimates_rooms_list": "GET /leads/{lead_id}/estimates/{estimate_id}/rooms",
        "movescout_estimates_rooms_create": "POST /leads/{lead_id}/estimates/{estimate_id}/rooms",
        "movescout_estimates_articles_catalog": "GET /leads/{lead_id}/estimates/{estimate_id}/rooms/{room_id}/articles",
        "movescout_estimates_articles_create": "POST /leads/{lead_id}/estimates/{estimate_id}/rooms/{room_id}/articles",
        "movescout_estimates_inventory_lines_update": "PUT /leads/{lead_id}/estimates/{estimate_id}/inventory/lines",
        "movescout_estimates_inventory_save": "POST /leads/{lead_id}/estimates/{estimate_id}/inventory/save",
        "movescout_estimates_pricing_get": "GET /leads/{lead_id}/estimates/{estimate_id}/pricing",
        "movescout_estimates_pricing_calculate": "POST /leads/{lead_id}/estimates/{estimate_id}/calculate-pricing",
        "movescout_estimates_tariff_effective": "GET /leads/{lead_id}/estimates/{estimate_id}/tariff-effective",
        "movescout_reference_lov": "GET /lov",
        "movescout_reference_service_items": "GET /reference/service-items",
        "movescout_reference_price_classes": "GET /reference/price-classes",
        "movescout_reference_move_coordinators": "GET /reference/move-coordinators",
        "movescout_reference_custom_tariffs": "GET /reference/custom-tariffs",
        "movescout_reference_lead_source_programs": "GET /reference/lead-source-programs",
        "movescout_reference_agents": "GET /reference/agents",
        "movescout_inventory_get": "GET /leads/{lead_id}/inventory",
    }

    print("=" * 60)
    print("Parity Verification:")
    print("-" * 40)
    
    mcp_tool_names = {name for name, _ in mcp_tools}
    missing_tools = set(expected_tools.keys()) - mcp_tool_names
    extra_tools = mcp_tool_names - set(expected_tools.keys())
    
    if missing_tools:
        print(f"MISSING MCP tools: {missing_tools}")
    if extra_tools:
        print(f"EXTRA MCP tools (not in expected mapping): {extra_tools}")
    
    if not missing_tools and not extra_tools:
        print(f"✓ All {len(expected_tools)} expected MCP tools present")
    
    print()
    print(f"Total MCP tools: {len(mcp_tools)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
