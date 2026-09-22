# MoveScout MCP Server

MCP (Model Context Protocol) server for MoveScout middleware. Provides tools for AI assistants to interact with MoveScout Pro through the middleware API.

## Architecture

```
AI Assistant (Cursor/Claude/Cloud Agent)
        ↓ MCP Protocol (stdio or HTTP)
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

## Transport Modes

| Mode | Use Case | Protocol |
|------|----------|----------|
| `http` (default) | Cloud agents, remote access | Streamable HTTP on `/mcp` |
| `stdio` | Local Cursor, SSH tunnel | JSON-RPC over stdin/stdout |

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MIDDLEWARE_URL` | Yes | `http://localhost:8000` | Middleware API URL |
| `MIDDLEWARE_API_KEY` | Yes | | API key for middleware authentication |
| `MCP_TRANSPORT` | No | `http` | Transport mode: `http` or `stdio` |
| `MCP_HTTP_PORT` | No | `8080` | HTTP server port (http mode only) |
| `MCP_HTTP_TOKEN` | Yes* | | Bearer token for HTTP auth (*required for http mode) |

## Deployment (TrueNAS)

### 1. Environment Variables

Add to your `.env` file:

```bash
# Middleware API key (create via scripts/create_user.py)
MCP_API_KEY=your-middleware-api-key

# HTTP auth token (generate a strong random string)
MCP_HTTP_TOKEN=your-secret-token-here

# Transport mode
MCP_TRANSPORT=http

# Host port (default 8788 - port 8080 is used by nginx on TrueNAS)
MCP_HOST_PORT=8788
```

### 2. Docker Compose

The MCP service is already configured in `deploy/docker-compose.yml`:

```yaml
services:
  mcp:
    build:
      context: ../mcp
      dockerfile: Dockerfile
    ports:
      - "${MCP_HOST_PORT:-8788}:8080"  # Host port 8788, container port 8080
    environment:
      MIDDLEWARE_URL: http://api:8000
      MIDDLEWARE_API_KEY: ${MCP_API_KEY:-}
      MCP_TRANSPORT: ${MCP_TRANSPORT:-http}
      MCP_HTTP_PORT: 8080
      MCP_HTTP_TOKEN: ${MCP_HTTP_TOKEN:-}
    depends_on:
      - api
    restart: unless-stopped
```

**Note:** Host port 8080 is typically used by nginx on TrueNAS. Default host port is **8788**. Override with `MCP_HOST_PORT` in `.env` if needed.

### 3. Nginx Proxy Manager (NPM)

For public HTTPS access via NPM on TrueNAS:

1. **Add Proxy Host:**
   - Domain: `mspmcp.jbeckstead.com`
   - Forward Hostname/IP: `192.168.68.5` (TrueNAS LAN IP)
   - Forward Port: `8788`
   - Enable SSL (Let's Encrypt)
   - Enable WebSocket support

2. **Custom Nginx Configuration** (Advanced tab):
   ```nginx
   proxy_buffering off;
   proxy_cache off;
   chunked_transfer_encoding on;
   proxy_read_timeout 3600s;
   proxy_send_timeout 3600s;
   ```

For standalone nginx, see `deploy/nginx/mspmcp.jbeckstead.com.conf.example`.

### 4. Firewall

- Open WAN → 443 (HTTPS) only
- Do NOT expose port 8788 directly to WAN

## Cursor Configuration

### Remote HTTP (Cloud Agents)

For Cursor cloud agents, add in Dashboard → Integrations & MCP:

- **URL:** `https://mspmcp.jbeckstead.com/mcp`
- **Transport:** HTTP (Streamable HTTP)
- **Headers:** `Authorization: Bearer YOUR_MCP_HTTP_TOKEN`

### Remote HTTP (Local Cursor)

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "movescout": {
      "url": "https://mspmcp.jbeckstead.com/mcp",
      "transport": "http",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_HTTP_TOKEN"
      }
    }
  }
}
```

### Local stdio (SSH Tunnel - Optional)

For local Cursor with SSH access to TrueNAS:

```json
{
  "mcpServers": {
    "movescout": {
      "command": "ssh",
      "args": [
        "truenas",
        "docker", "exec", "-i", "deploy-mcp-1",
        "python", "server.py"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio"
      },
      "transport": "stdio"
    }
  }
}
```

## Endpoints

| Path | Method | Auth | Description |
|------|--------|------|-------------|
| `/health` | GET | No | Health check (returns `{"status": "ok"}`) |
| `/mcp` | POST | Yes | MCP Streamable HTTP endpoint |

## Authentication

HTTP mode requires Bearer token authentication:

```
Authorization: Bearer YOUR_MCP_HTTP_TOKEN
```

Unauthenticated requests return `401 Unauthorized`:

```json
{"error": "Missing or invalid Authorization header"}
```

The `/health` endpoint is exempt from authentication for load balancer probes.

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

## Development

Local testing:

```bash
cd mcp
pip install -r requirements.txt

# HTTP mode (default)
export MIDDLEWARE_URL=http://localhost:8000
export MIDDLEWARE_API_KEY=your-api-key
export MCP_HTTP_TOKEN=test-token
python server.py

# Test health
curl http://localhost:8080/health

# Test auth rejection
curl http://localhost:8080/mcp  # Returns 401

# Test with auth
curl -H "Authorization: Bearer test-token" http://localhost:8080/mcp
```

For stdio mode:

```bash
export MCP_TRANSPORT=stdio
python server.py
```
