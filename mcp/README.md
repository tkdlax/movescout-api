# MoveScout MCP Server

MCP (Model Context Protocol) server for MoveScout middleware. Provides tools for AI assistants to interact with MoveScout Pro through the middleware API.

## Architecture

```
AI Assistant (Cursor/Claude)
        ↓
   MCP Server (this)
        ↓ HTTP + X-API-Key
   Middleware API
        ↓ Bearer token
   MoveScout Pro API
```

The MCP server is a thin proxy that:
1. Receives tool calls from AI assistants via MCP protocol
2. Maps them to middleware HTTP calls
3. Returns structured JSON responses

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `MIDDLEWARE_URL` | Yes | Middleware API URL (e.g., `http://api:8000` or `https://mspapi.jbeckstead.com`) |
| `MIDDLEWARE_API_KEY` | Yes | API key for middleware authentication |

## Deployment (TrueNAS)

Add to your `docker-compose.yml`:

```yaml
services:
  mcp:
    build:
      context: ./mcp
      dockerfile: Dockerfile
    environment:
      MIDDLEWARE_URL: http://api:8000
      MIDDLEWARE_API_KEY: ${MCP_API_KEY}
    depends_on:
      - api
    # For stdio transport (default):
    stdin_open: true
    tty: true
```

For HTTP/SSE transport, add port mapping:

```yaml
    ports:
      - "8080:8080"
```

## Cursor Configuration

Add to Cursor settings (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "movescout": {
      "command": "docker",
      "args": ["exec", "-i", "movescout-mcp", "python", "server.py"],
      "transport": "stdio"
    }
  }
}
```

Or for remote HTTP server:

```json
{
  "mcpServers": {
    "movescout": {
      "url": "https://mspmcp.jbeckstead.com",
      "transport": "sse"
    }
  }
}
```

## Available Tools

### Lead Management
- `movescout_leads_list` — List leads with pagination and filters
- `movescout_leads_get` — Get a single lead by ID
- `movescout_leads_create` — Create a new lead
- `movescout_leads_update` — Update an existing lead
- `movescout_leads_move_type` — Get move type based on origin/destination

### Activities
- `movescout_activities_list` — List activities for a lead
- `movescout_activities_get` — Get a single activity by ID
- `movescout_activities_create` — Create an activity for a lead

### Estimates
- `movescout_estimates_list` — List estimates for a lead
- `movescout_estimates_get_primary` — Get the primary estimate
- `movescout_estimates_get` — Get estimate details
- `movescout_estimates_create` — Create an estimate
- `movescout_estimates_update` — Update an estimate

### Rooms & Articles
- `movescout_estimates_rooms_list` — List rooms for an estimate
- `movescout_estimates_rooms_create` — Create a room
- `movescout_estimates_articles_catalog` — Get article catalog for a room
- `movescout_estimates_articles_create` — Create a custom article

### Inventory
- `movescout_estimates_inventory_lines_update` — Update inventory lines
- `movescout_estimates_inventory_save` — Save inventory changes
- `movescout_inventory_get` — Get room-grouped inventory (hero endpoint)

### Pricing
- `movescout_estimates_pricing_get` — Get pricing totals
- `movescout_estimates_pricing_calculate` — Calculate pricing
- `movescout_estimates_tariff_effective` — Get tariff by effective date

### Reference Data
- `movescout_reference_lov` — Get list of values
- `movescout_reference_service_items` — Get service items
- `movescout_reference_price_classes` — Get price classes
- `movescout_reference_move_coordinators` — Get move coordinators
- `movescout_reference_custom_tariffs` — Get custom tariffs
- `movescout_reference_lead_source_programs` — Get lead source programs
- `movescout_reference_agents` — Get all Sirva agents

## MCP ↔ Middleware Parity

Every MCP tool maps 1:1 to a middleware route. To verify parity:

```bash
python scripts/check_mcp_parity.py
```

This script compares FastAPI routes with MCP tool definitions and reports any mismatches.

## Development

Local testing:

```bash
cd mcp
pip install -r requirements.txt

# Set environment
export MIDDLEWARE_URL=http://localhost:8000
export MIDDLEWARE_API_KEY=your-api-key

# Run server
python server.py
```

The server uses stdio transport by default, reading JSON-RPC messages from stdin and writing responses to stdout.
