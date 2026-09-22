"""MoveScout MCP tool definitions.

Each tool maps 1:1 to a middleware REST route.
"""

from typing import Any

import httpx
from mcp.types import Tool


def _tool(name: str, description: str, properties: dict, required: list[str] | None = None) -> Tool:
    """Helper to create a Tool with input schema."""
    return Tool(
        name=name,
        description=description,
        inputSchema={
            "type": "object",
            "properties": properties,
            "required": required or [],
        },
    )


TOOLS: list[Tool] = [
    _tool(
        "movescout_leads_list",
        "List leads with pagination and optional filters",
        {
            "page": {"type": "integer", "description": "Page number (1-indexed)", "default": 1},
            "maxResultSize": {"type": "integer", "description": "Results per page", "default": 500},
            "defaultFilter": {"type": "integer", "description": "Lead filter (0-12)", "default": 3},
            "sortField": {"type": "string", "description": "Field to sort by"},
            "sortDir": {"type": "string", "description": "Sort direction (asc/desc)", "default": "desc"},
        },
    ),
    _tool(
        "movescout_leads_get",
        "Get a single lead by ID",
        {"leadId": {"type": "string", "description": "Lead ID"}},
        ["leadId"],
    ),
    _tool(
        "movescout_leads_create",
        "Create a new lead",
        {"lead": {"type": "object", "description": "Lead data"}},
        ["lead"],
    ),
    _tool(
        "movescout_leads_update",
        "Update an existing lead",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "lead": {"type": "object", "description": "Lead data to update"},
        },
        ["leadId", "lead"],
    ),
    _tool(
        "movescout_leads_move_type",
        "Get move type (Interstate/Intrastate/Local) based on origin/destination",
        {
            "originState": {"type": "string", "description": "Origin state code"},
            "destinationState": {"type": "string", "description": "Destination state code"},
            "originCountry": {"type": "string", "description": "Origin country code", "default": "US"},
            "destinationCountry": {"type": "string", "description": "Destination country code", "default": "US"},
        },
        ["originState", "destinationState"],
    ),
    _tool(
        "movescout_activities_list",
        "List activities for a lead",
        {"leadId": {"type": "string", "description": "Lead ID"}},
        ["leadId"],
    ),
    _tool(
        "movescout_activities_get",
        "Get a single activity by ID",
        {"activityId": {"type": "string", "description": "Activity ID"}},
        ["activityId"],
    ),
    _tool(
        "movescout_activities_create",
        "Create an activity for a lead",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "activity": {"type": "object", "description": "Activity data"},
        },
        ["leadId", "activity"],
    ),
    _tool(
        "movescout_estimates_list",
        "List estimates for a lead",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "page": {"type": "integer", "description": "Page number", "default": 1},
            "maxResultSize": {"type": "integer", "description": "Results per page", "default": 15},
        },
        ["leadId"],
    ),
    _tool(
        "movescout_estimates_get_primary",
        "Get the primary estimate for a lead",
        {"leadId": {"type": "string", "description": "Lead ID"}},
        ["leadId"],
    ),
    _tool(
        "movescout_estimates_get",
        "Get estimate details",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
        },
        ["leadId", "estimateId"],
    ),
    _tool(
        "movescout_estimates_create",
        "Create an estimate (with or without inventory)",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimate": {"type": "object", "description": "Estimate data"},
        },
        ["leadId", "estimate"],
    ),
    _tool(
        "movescout_estimates_update",
        "Update an existing estimate",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "estimate": {"type": "object", "description": "Estimate data to update"},
        },
        ["leadId", "estimateId", "estimate"],
    ),
    _tool(
        "movescout_estimates_rooms_list",
        "List rooms for an estimate",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
        },
        ["leadId", "estimateId"],
    ),
    _tool(
        "movescout_estimates_rooms_create",
        "Create a room for an estimate",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "room": {"type": "object", "description": "Room data"},
        },
        ["leadId", "estimateId", "room"],
    ),
    _tool(
        "movescout_estimates_articles_catalog",
        "Get article catalog for a room",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "roomId": {"type": "integer", "description": "Room ID"},
        },
        ["leadId", "estimateId", "roomId"],
    ),
    _tool(
        "movescout_estimates_articles_create",
        "Create a custom article for a room",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "roomId": {"type": "integer", "description": "Room ID"},
            "article": {"type": "object", "description": "Article data"},
        },
        ["leadId", "estimateId", "roomId", "article"],
    ),
    _tool(
        "movescout_estimates_inventory_lines_update",
        "Update inventory line items",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "lines": {"type": "array", "description": "Inventory line items"},
        },
        ["leadId", "estimateId", "lines"],
    ),
    _tool(
        "movescout_estimates_inventory_save",
        "Save/commit inventory changes",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "density": {"type": "integer", "description": "Density value", "default": 7},
        },
        ["leadId", "estimateId"],
    ),
    _tool(
        "movescout_estimates_pricing_get",
        "Get pricing totals for an estimate",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
        },
        ["leadId", "estimateId"],
    ),
    _tool(
        "movescout_estimates_pricing_calculate",
        "Calculate pricing for an estimate",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "pricingRequest": {"type": "object", "description": "Pricing request data"},
        },
        ["leadId", "estimateId", "pricingRequest"],
    ),
    _tool(
        "movescout_estimates_tariff_effective",
        "Get tariff details by effective date",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "tariffId": {"type": "integer", "description": "Tariff ID"},
            "tariffName": {"type": "string", "description": "Tariff name"},
        },
        ["leadId", "estimateId", "tariffId", "tariffName"],
    ),
    _tool(
        "movescout_reference_lov",
        "Get list of values (enums)",
        {"refresh": {"type": "boolean", "description": "Force refresh cache", "default": False}},
    ),
    _tool(
        "movescout_reference_service_items",
        "Get alliance service items",
        {"refresh": {"type": "boolean", "description": "Force refresh cache", "default": False}},
    ),
    _tool(
        "movescout_reference_price_classes",
        "Get price classes for a booker",
        {"bookerId": {"type": "string", "description": "Booker/agency ID"}},
        ["bookerId"],
    ),
    _tool(
        "movescout_reference_move_coordinators",
        "Get move coordinators for an agency",
        {"agencyId": {"type": "integer", "description": "Agency ID"}},
        ["agencyId"],
    ),
    _tool(
        "movescout_reference_custom_tariffs",
        "Get custom tariffs for a brand",
        {"brandId": {"type": "integer", "description": "Brand ID"}},
        ["brandId"],
    ),
    _tool(
        "movescout_reference_lead_source_programs",
        "Get lead source programs for an agency",
        {
            "agencyId": {"type": "integer", "description": "Agency ID"},
            "page": {"type": "integer", "description": "Page number", "default": 1},
            "maxResultSize": {"type": "integer", "description": "Results per page", "default": 100},
        },
        ["agencyId"],
    ),
    _tool(
        "movescout_reference_agents",
        "Get all Sirva network agents",
        {"refresh": {"type": "boolean", "description": "Force refresh cache", "default": False}},
    ),
    _tool(
        "movescout_inventory_get",
        "Get room-grouped inventory for a lead (hero endpoint)",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Optional estimate ID"},
            "includeSummary": {"type": "boolean", "description": "Include summary", "default": True},
            "shippingOnly": {"type": "boolean", "description": "Shipping items only", "default": False},
        },
        ["leadId"],
    ),
]


async def execute_tool(client: httpx.AsyncClient, name: str, arguments: dict[str, Any]) -> Any:
    """Execute an MCP tool by calling the appropriate middleware endpoint."""
    
    routes = {
        "movescout_leads_list": lambda a: client.get("/leads", params={
            "page": a.get("page", 1),
            "maxResultSize": a.get("maxResultSize", 500),
            "defaultFilter": a.get("defaultFilter", 3),
            "sortField": a.get("sortField"),
            "sortDir": a.get("sortDir", "desc"),
        }),
        "movescout_leads_get": lambda a: client.get(f"/leads/{a['leadId']}"),
        "movescout_leads_create": lambda a: client.post("/leads", json=a["lead"]),
        "movescout_leads_update": lambda a: client.put(f"/leads/{a['leadId']}", json=a["lead"]),
        "movescout_leads_move_type": lambda a: client.get("/leads/move-type", params={
            "originState": a["originState"],
            "destinationState": a["destinationState"],
            "originCountry": a.get("originCountry", "US"),
            "destinationCountry": a.get("destinationCountry", "US"),
        }),
        "movescout_activities_list": lambda a: client.get(f"/leads/{a['leadId']}/appointments"),
        "movescout_activities_get": lambda a: client.get(f"/activities/{a['activityId']}"),
        "movescout_activities_create": lambda a: client.post(
            f"/leads/{a['leadId']}/activities", json=a["activity"]
        ),
        "movescout_estimates_list": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates",
            params={"page": a.get("page", 1), "maxResultSize": a.get("maxResultSize", 15)},
        ),
        "movescout_estimates_get_primary": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/primary"
        ),
        "movescout_estimates_get": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}"
        ),
        "movescout_estimates_create": lambda a: client.post(
            f"/leads/{a['leadId']}/estimates", json=a["estimate"]
        ),
        "movescout_estimates_update": lambda a: client.put(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}", json=a["estimate"]
        ),
        "movescout_estimates_rooms_list": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/rooms"
        ),
        "movescout_estimates_rooms_create": lambda a: client.post(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/rooms", json=a["room"]
        ),
        "movescout_estimates_articles_catalog": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/rooms/{a['roomId']}/articles"
        ),
        "movescout_estimates_articles_create": lambda a: client.post(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/rooms/{a['roomId']}/articles",
            json=a["article"],
        ),
        "movescout_estimates_inventory_lines_update": lambda a: client.put(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/inventory/lines",
            json=a["lines"],
        ),
        "movescout_estimates_inventory_save": lambda a: client.post(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/inventory/save",
            params={"density": a.get("density", 7)},
        ),
        "movescout_estimates_pricing_get": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/pricing"
        ),
        "movescout_estimates_pricing_calculate": lambda a: client.post(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/calculate-pricing",
            json=a["pricingRequest"],
        ),
        "movescout_estimates_tariff_effective": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/tariff-effective",
            params={"tariffId": a["tariffId"], "tariffName": a["tariffName"]},
        ),
        "movescout_reference_lov": lambda a: client.get(
            "/lov", params={"refresh": a.get("refresh", False)}
        ),
        "movescout_reference_service_items": lambda a: client.get(
            "/reference/service-items", params={"refresh": a.get("refresh", False)}
        ),
        "movescout_reference_price_classes": lambda a: client.get(
            "/reference/price-classes", params={"bookerId": a["bookerId"]}
        ),
        "movescout_reference_move_coordinators": lambda a: client.get(
            "/reference/move-coordinators", params={"agencyId": a["agencyId"]}
        ),
        "movescout_reference_custom_tariffs": lambda a: client.get(
            "/reference/custom-tariffs", params={"brandId": a["brandId"]}
        ),
        "movescout_reference_lead_source_programs": lambda a: client.get(
            "/reference/lead-source-programs",
            params={
                "agencyId": a["agencyId"],
                "page": a.get("page", 1),
                "maxResultSize": a.get("maxResultSize", 100),
            },
        ),
        "movescout_reference_agents": lambda a: client.get(
            "/reference/agents", params={"refresh": a.get("refresh", False)}
        ),
        "movescout_inventory_get": lambda a: client.get(
            f"/leads/{a['leadId']}/inventory",
            params={
                "estimateId": a.get("estimateId"),
                "includeSummary": a.get("includeSummary", True),
                "shippingOnly": a.get("shippingOnly", False),
            },
        ),
    }

    if name not in routes:
        raise ValueError(f"Unknown tool: {name}")

    response = await routes[name](arguments)
    response.raise_for_status()
    return response.json()
