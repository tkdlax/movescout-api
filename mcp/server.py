"""MoveScout MCP Server.

Provides MCP tools that map 1:1 to middleware REST routes.
Supports both stdio (local) and HTTP/Streamable HTTP (remote/cloud) transports.

Environment variables:
  MIDDLEWARE_URL      - URL of the middleware API (default: http://localhost:8000)
  MIDDLEWARE_API_KEY  - API key for middleware authentication
  MCP_TRANSPORT       - Transport mode: "stdio" or "http" (default: http)
  MCP_HTTP_PORT       - HTTP port to listen on (default: 8080)
  MCP_HTTP_TOKEN      - Bearer token for HTTP authentication (required for http mode)
"""

import json
import logging
import os
from typing import Any

import httpx
import uvicorn
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequestParams,
    CallToolResult,
    ListToolsResult,
    TextContent,
)
from mcp_types._types import PaginatedRequestParams
from starlette.requests import Request
from starlette.responses import JSONResponse
from tools import TOOLS, execute_tool

logger = logging.getLogger(__name__)

MIDDLEWARE_URL = os.environ.get("MIDDLEWARE_URL", "http://localhost:8000")
MIDDLEWARE_API_KEY = os.environ.get("MIDDLEWARE_API_KEY", "")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "http").lower()
MCP_HTTP_PORT = int(os.environ.get("MCP_HTTP_PORT", "8080"))
MCP_HTTP_TOKEN = os.environ.get("MCP_HTTP_TOKEN", "")


def create_http_client() -> httpx.AsyncClient:
    """Create an HTTP client for middleware calls."""
    return httpx.AsyncClient(
        base_url=MIDDLEWARE_URL,
        headers={"X-API-Key": MIDDLEWARE_API_KEY},
        timeout=httpx.Timeout(120.0, connect=10.0),
    )


server = Server("movescout-mcp")


async def handle_list_tools(ctx: Any, params: PaginatedRequestParams) -> ListToolsResult:
    """Return the list of available MCP tools."""
    return ListToolsResult(tools=TOOLS)


async def handle_call_tool(ctx: Any, params: CallToolRequestParams) -> CallToolResult:
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


async def health_endpoint(request: Request) -> JSONResponse:
    """Health check endpoint - no auth required."""
    return JSONResponse({"status": "ok", "server": "movescout-mcp"})


def make_auth_asgi_middleware(app, token: str | None):
    """Create an ASGI middleware that adds Bearer auth.
    
    This is a pure ASGI wrapper that:
    1. Handles /health without auth
    2. Checks Bearer token for all other paths
    3. Passes lifespan events through unchanged
    
    Critical: We must pass 'lifespan' scope through unchanged so the
    MCP session manager can initialize properly.
    """
    async def middleware(scope, receive, send):
        # Pass lifespan scope through unchanged - this is critical!
        if scope["type"] == "lifespan":
            await app(scope, receive, send)
            return
        
        if scope["type"] == "http":
            path = scope.get("path", "")
            
            # Health check - no auth required
            if path == "/health":
                response = JSONResponse({"status": "ok", "server": "movescout-mcp"})
                await response(scope, receive, send)
                return
            
            # Check auth for all other paths if token is configured
            if token:
                headers = dict(scope.get("headers", []))
                auth_header = headers.get(b"authorization", b"").decode()
                
                if not auth_header.lower().startswith("bearer "):
                    response = JSONResponse(
                        {"error": "Missing or invalid Authorization header"},
                        status_code=401,
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                    await response(scope, receive, send)
                    return
                
                provided_token = auth_header[7:]  # Remove "Bearer " prefix
                if provided_token != token:
                    response = JSONResponse(
                        {"error": "Invalid token"},
                        status_code=401,
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                    await response(scope, receive, send)
                    return
        
        # Pass through to the app
        await app(scope, receive, send)
    
    return middleware


def create_http_app():
    """Create the HTTP app with authentication.
    
    Uses the MCP SDK's streamable_http_app directly and wraps it with
    a simple ASGI middleware for auth. The middleware passes lifespan
    events through unchanged so the MCP session manager initializes.
    """
    # Create the MCP app
    mcp_app = server.streamable_http_app(
        streamable_http_path="/mcp",
        host="0.0.0.0",
    )
    
    if not MCP_HTTP_TOKEN:
        logger.warning("MCP_HTTP_TOKEN not set - HTTP endpoints are UNAUTHENTICATED")
        # Still wrap to add health endpoint
        return make_auth_asgi_middleware(mcp_app, None)
    
    return make_auth_asgi_middleware(mcp_app, MCP_HTTP_TOKEN)


async def run_stdio():
    """Run the MCP server over stdio."""
    logger.info("Starting MoveScout MCP Server (stdio mode)")
    logger.info(f"Middleware URL: {MIDDLEWARE_URL}")

    if not MIDDLEWARE_API_KEY:
        logger.warning("MIDDLEWARE_API_KEY not set - tool calls will fail")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run_http():
    """Run the MCP server over HTTP/Streamable HTTP."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("Starting MoveScout MCP Server (HTTP mode)")
    logger.info(f"Middleware URL: {MIDDLEWARE_URL}")
    logger.info(f"Listening on port {MCP_HTTP_PORT}")
    logger.info(f"MCP endpoint: http://0.0.0.0:{MCP_HTTP_PORT}/mcp")

    if not MIDDLEWARE_API_KEY:
        logger.warning("MIDDLEWARE_API_KEY not set - tool calls will fail")

    if not MCP_HTTP_TOKEN:
        logger.warning("MCP_HTTP_TOKEN not set - HTTP endpoints are UNAUTHENTICATED")

    app = create_http_app()
    uvicorn.run(app, host="0.0.0.0", port=MCP_HTTP_PORT, log_level="info")


async def run_stdio_main():
    """Run the MCP server over stdio (async entrypoint)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    await run_stdio()


def main():
    """Run the MCP server in the configured transport mode."""
    if MCP_TRANSPORT == "stdio":
        import asyncio
        asyncio.run(run_stdio_main())
    elif MCP_TRANSPORT == "http":
        run_http()
    else:
        logging.basicConfig(level=logging.ERROR)
        logger.error(f"Unknown transport: {MCP_TRANSPORT}. Use 'stdio' or 'http'.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
