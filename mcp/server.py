"""MoveScout MCP Server.

Provides MCP tools that map 1:1 to middleware REST routes.
The server calls the middleware API over HTTP with X-API-Key authentication.
"""

import json
import logging
import os
from typing import Any

import httpx
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    CallToolRequestParams,
    ListToolsResult,
    TextContent,
)
from mcp_types._types import PaginatedRequestParams

from tools import TOOLS, execute_tool

logger = logging.getLogger(__name__)

MIDDLEWARE_URL = os.environ.get("MIDDLEWARE_URL", "http://localhost:8000")
MIDDLEWARE_API_KEY = os.environ.get("MIDDLEWARE_API_KEY", "")


def create_http_client() -> httpx.AsyncClient:
    """Create an HTTP client for middleware calls."""
    return httpx.AsyncClient(
        base_url=MIDDLEWARE_URL,
        headers={"X-API-Key": MIDDLEWARE_API_KEY},
        timeout=httpx.Timeout(120.0, connect=10.0),
    )


server = Server("movescout-mcp")


async def handle_list_tools(params: PaginatedRequestParams) -> ListToolsResult:
    """Return the list of available MCP tools."""
    return ListToolsResult(tools=TOOLS)


async def handle_call_tool(params: CallToolRequestParams) -> CallToolResult:
    """Execute an MCP tool by calling the middleware API."""
    async with create_http_client() as client:
        try:
            result = await execute_tool(client, params.name, params.arguments or {})
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, indent=2))]
            )
        except httpx.HTTPStatusError as exc:
            error_detail = exc.response.text[:500] if exc.response.text else str(exc)
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {error_detail}")],
                isError=True,
            )
        except Exception as exc:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {exc}")],
                isError=True,
            )


server.add_request_handler("tools/list", PaginatedRequestParams, handle_list_tools)
server.add_request_handler("tools/call", CallToolRequestParams, handle_call_tool)


async def main():
    """Run the MCP server over stdio."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting MoveScout MCP Server")
    logger.info(f"Middleware URL: {MIDDLEWARE_URL}")

    if not MIDDLEWARE_API_KEY:
        logger.warning("MIDDLEWARE_API_KEY not set - tool calls will fail")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
