# MoveScout MCP + Middleware Expansion Plan

**Date:** 2026-09-22  
**Status:** In Progress  
**Source:** `movescout-exploration-slim.tar.gz` (Flows 01–03, catalogs)

---

## Executive Summary

This plan expands the MoveScout middleware (`tkdlax/movescout-api`) with write endpoints for leads, activities, estimates, rooms, articles, and inventory operations—all derived from captured MoveScout Pro internal API traffic. A companion MCP server will be scaffolded in the same repository, deployable alongside the API on TrueNAS. MCP tools will be 1:1 with implemented middleware routes.

---

## Phase A: Attack Order for Middleware Writes

Priority based on capture completeness and workflow dependencies:

### Tier 1 — Foundation Writes (Solid Captures)

| # | Capability | Upstream Endpoint | Middleware Route | Flow/Call |
|---|------------|-------------------|------------------|-----------|
| 1 | Get move type | `GET Lead/GetMoveType` | `GET /leads/move-type` | 01/001 |
| 2 | Create/update lead | `POST Lead/CreateOrUpdateLead` | `POST /leads` / `PUT /leads/{id}` | 01/003 (already exists) |
| 3 | Create/update activity | `POST Activity/CreateOrUpdateActivity` | `POST /leads/{id}/activities` | 01/010, 01/012 |
| 4 | Get all activities | `POST Activity/GetAllActivitiesWithCombineData` | `GET /leads/{id}/activities` | 01/013 |
| 5 | Get activity by ID | `GET Activity/GetActivityById` | `GET /activities/{id}` | 01/014 |

### Tier 2 — Estimate + Inventory Writes

| # | Capability | Upstream Endpoint | Middleware Route | Flow/Call |
|---|------------|-------------------|------------------|-----------|
| 6 | Create estimate with inventory | `POST Inventory/CreateOrUpdateEstimates` | `POST /leads/{id}/estimates` | 02/001 |
| 7 | Create/update room | `POST Inventory/CreateOrUpdateRoom` | `POST .../estimates/{eid}/rooms` | 02/002-004 |
| 8 | Create custom article | `POST Inventory/CreateArticleFromInventory` | `POST .../rooms/{rid}/articles` | 02/005-007 |
| 9 | Update inventory lines | `POST Inventory/CreateOrUpdateArticleForListInventory` | `PUT .../inventory/lines` | 02/008 |
| 10 | Save estimate inventory | `POST InventoryCommon/SaveEstimateWithTrueFlag` | `POST .../estimates/{eid}/inventory/save` | 02/009 |
| 11 | Update lead estimate | `PUT Estimate/UpdateLeadEstimate` | `PUT .../estimates/{eid}` | 01/034, 02/010 |
| 12 | Calculate pricing | `POST Estimate/CalculateEstimationPricing` | `POST .../estimates/{eid}/calculate-pricing` | 02/014 |

### Tier 3 — Catalog/Reference Reads (Missing)

| # | Capability | Upstream Endpoint | Middleware Route | Flow/Call |
|---|------------|-------------------|------------------|-----------|
| 13 | Move coordinators | `GET Dropdown/GetMoveCoordinatorListBasedOnAgencyId` | `GET /reference/move-coordinators` | 01/032, 03/003 |
| 14 | CT list for estimate | `GET CustomTariffAPIService/GetCTListForEstimate` | `GET /reference/custom-tariffs` | 01/029, 03/001 |
| 15 | Articles by room | `GET Inventory/GetAllArticlesGroupByRoomSP` | `GET .../estimates/{eid}/rooms/{rid}/articles` | 03/001-005 |
| 16 | Tariff by effective date | `GET GetEstimate/GetEstimateTariffByEffectiveDate` | `GET .../estimates/{eid}/tariff-effective` | 01/030, 02/013 |
| 17 | Lead source programs | `GET LeadSourceProgram/GetPaginatedLeadSourceProgramByAgencyId` | `GET /reference/lead-source-programs` | 01/007 |
| 18 | Price levels (from LOV) | Already in `/lov` | Filter helper | 03/lov-catalog |

### Known Gaps (Skip This Pass)

- **Flow 01/015 — Create estimate without inventory**: Request body not recovered; skip until re-captured
- **Flow 03 Room 69 (SIT)**: Empty response; catalog gap, not API gap
- **P1–P10 new UI captures**: Await Jake's authorization before probing

---

## Phase B: MCP Architecture

### Deployment Model

```
┌──────────────────────────────────────────────────────────┐
│                  TrueNAS Docker Compose                  │
├────────────────┬────────────────┬────────────────────────┤
│    postgres    │      api       │         mcp            │
│  (port 5432)   │  (port 8000)   │     (port 8080)        │
└────────────────┴────────────────┴────────────────────────┘
                         │                   │
                         ▼                   ▼
                 ┌───────────────────────────────────────┐
                 │          Nginx Proxy Manager          │
                 │  mspapi.jbeckstead.com → :8000        │
                 │  mspmcp.jbeckstead.com → :8080        │
                 └───────────────────────────────────────┘
```

### Container Structure

- **`mcp/`** — New service directory in repo root
  - `server.py` — MCP server implementation (stdio or HTTP)
  - `tools.py` — Tool definitions mapped 1:1 from FastAPI routes
  - `Dockerfile` — Python base + MCP dependencies
- Compose service `mcp` in `deploy/docker-compose.yml`

### Tool Generation Strategy

**Hand-mapped 1:1 from FastAPI routes** (not auto-generated):
- Each MCP tool corresponds to exactly one middleware route
- Tool names follow pattern: `movescout_<resource>_<action>`
- Parameters mirror FastAPI route params + query params + body schema

Example mapping:
```
FastAPI: POST /leads/{lead_id}/estimates
MCP: movescout_estimates_create(lead_id, body)
```

---

## Phase C: Auth Model for MCP

### Principles

1. **Reuse middleware API keys** — MCP server calls middleware over HTTP with `X-API-Key`
2. **Never expose MoveScout passwords** — MCP clients only see middleware API keys
3. **Environment-based config** — `MIDDLEWARE_URL`, `MIDDLEWARE_API_KEY` in MCP container

### Auth Flow

```
MCP Client → MCP Server → Middleware (X-API-Key) → MoveScout (Bearer token)
```

MCP server is a thin proxy that:
1. Receives tool calls from Cursor/Claude
2. Maps to middleware HTTP calls
3. Returns structured responses

---

## Phase D: TrueNAS Deploy Notes

### Compose Service Addition

Add to `deploy/docker-compose.yml`:

```yaml
services:
  # ... existing postgres, api ...
  
  mcp:
    build:
      context: ../mcp
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      MIDDLEWARE_URL: http://api:8000
      MIDDLEWARE_API_KEY: ${MCP_API_KEY}
    depends_on:
      - api
```

### Nginx Proxy Manager

Add new proxy host:
- Domain: `mspmcp.jbeckstead.com`
- Forward: `truenas-ip:8080`
- TLS via Let's Encrypt

### Upgrade Path

1. `git pull` in dataset
2. `docker compose up -d --build` (builds new `mcp` image)
3. Add NPM proxy host if first deploy
4. Create dedicated API key for MCP: `python scripts/create_user.py --name "MCP Server"`

### Pointing Cursor at MCP

In Cursor settings, add MCP server:
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

---

## Phase E: MCP ↔ Middleware Parity Rule

### Hard Rule

> **No MCP tool without a live, tested middleware route.**

### PR Checklist Item

Every PR that adds or modifies middleware routes must include:

- [ ] MCP tool added/updated in `mcp/tools.py`
- [ ] Tool maps 1:1 to middleware route
- [ ] Tool documented in MCP README
- [ ] Parity script passes: `python scripts/check_mcp_parity.py`

### Parity Script

`scripts/check_mcp_parity.py`:
- Enumerates FastAPI routes from `app.main:app`
- Enumerates MCP tools from `mcp.tools`
- Reports mismatches: routes without tools, tools without routes

---

## Implementation Checklist

### Middleware Routes

- [ ] `GET /leads/move-type` — GetMoveType
- [ ] `POST /leads/{id}/activities` — CreateOrUpdateActivity (survey)
- [ ] `GET /leads/{id}/activities` — GetAllActivitiesWithCombineData (route exists, verify)
- [ ] `GET /activities/{id}` — GetActivityById
- [ ] `POST /leads/{id}/estimates` — CreateOrUpdateEstimates (with inventory)
- [ ] `POST .../estimates/{eid}/rooms` — CreateOrUpdateRoom
- [ ] `POST .../rooms/{rid}/articles` — CreateArticleFromInventory
- [ ] `PUT .../inventory/lines` — CreateOrUpdateArticleForListInventory
- [ ] `POST .../estimates/{eid}/inventory/save` — SaveEstimateWithTrueFlag
- [ ] `PUT .../estimates/{eid}` — UpdateLeadEstimate
- [ ] `POST .../estimates/{eid}/calculate-pricing` — CalculateEstimationPricing
- [ ] `GET /reference/move-coordinators` — GetMoveCoordinatorListBasedOnAgencyId
- [ ] `GET /reference/custom-tariffs` — GetCTListForEstimate
- [ ] `GET .../estimates/{eid}/rooms/{rid}/articles` — GetAllArticlesGroupByRoomSP
- [ ] `GET .../estimates/{eid}/tariff-effective` — GetEstimateTariffByEffectiveDate
- [ ] `GET /reference/lead-source-programs` — GetPaginatedLeadSourceProgramByAgencyId

### MCP Scaffold

- [ ] `mcp/` directory structure
- [ ] `mcp/server.py` — MCP protocol implementation
- [ ] `mcp/tools.py` — Tool definitions
- [ ] `mcp/Dockerfile`
- [ ] Compose service in `deploy/docker-compose.yml`
- [ ] MCP README with setup instructions

### Documentation

- [ ] Update `docs/movescout-api-catalog.md` with new mappings
- [ ] Update main `README.md` with MCP section
- [ ] Add TrueNAS MCP deploy notes

### Tests/Fixtures

- [ ] Add fixtures from redacted captures
- [ ] Unit tests for new upstream client functions
- [ ] Integration test for MCP parity check

---

## Wired vs Blocked Summary

### Wired (Ready to Implement)

| Capability | Capture Quality | Notes |
|------------|-----------------|-------|
| GetMoveType | Complete | Simple GET with query params |
| CreateOrUpdateLead | Complete | Already implemented, verify |
| CreateOrUpdateActivity | Complete | Create + update variants captured |
| GetAllActivitiesWithCombineData | Complete | Verify existing route |
| GetActivityById | Complete | Simple GET |
| CreateOrUpdateEstimates | Complete | With inventory flag |
| CreateOrUpdateRoom | Complete | Multiple variants |
| CreateArticleFromInventory | Complete | Custom article creation |
| CreateOrUpdateArticleForListInventory | Complete | Inventory line updates |
| SaveEstimateWithTrueFlag | Complete | Commit inventory changes |
| UpdateLeadEstimate | Complete | Large payload, well-captured |
| CalculateEstimationPricing | Complete | 268-field request, full response |
| GetMoveCoordinatorListBasedOnAgencyId | Complete | Simple catalog |
| GetCTListForEstimate | Complete | Custom tariff list |
| GetAllArticlesGroupByRoomSP | Complete | 5 rooms captured |
| GetEstimateTariffByEffectiveDate | Complete | Tariff effective lookup |
| GetPaginatedLeadSourceProgramByAgencyId | Complete | Lead source programs |

### Blocked (Missing Captures)

| Capability | Gap | Resolution |
|------------|-----|------------|
| Create estimate without inventory | Request body lost (Flow 01/015) | Re-capture needed (P2) |
| Stock article add to inventory | P1 in progress | Await completion |
| Pricing variants (classes/levels/dates) | P3 planned | Await probing |
| Lead lifecycle updates | P4 planned | Await probing |
| Alliance/accessorial writes | P8 planned | Await probing |

---

---

## P1 Findings (2026-09-22)

### Solid Data from P1 Capture Pack

Flow 04 (`04-stock-articles-pricing/`) provides **inventory readback** confirming stock article lines on estimate `2395896`:

| articleId | Name | Room | roomId | qty | weight | cube | isCustomArticle | Line ID |
|-----------|------|------|--------|-----|--------|------|-----------------|---------|
| 870 | Air Conditioner | Living Room | 37 | 1 | 70 | 10 | **false** | 157950568 |
| 874 | Armoire | Master Bedroom | 39 | 1 | 210 | 30 | **false** | 157950569 |
| 879 | Bar, Stool | Bedroom 2 | 27 | 1 | 21 | 3 | **true** (!) | 157950570 |
| 318996 | Mattress | Test Bedroom | 78846 | 3 | 0 | 0 | true | 157909052 |

**Key observation:** Articles 870/874 are true **catalog stock** (`isCustomArticle: false`, `articleCode: V005/V010`). Article 879 is flagged `isCustomArticle: true` despite having a library-looking name and code — this indicates it was created via `CreateArticleFromInventory`, not added from the catalog.

**Pricing confirmed unchanged:** `GetEstimatePricingTotalJsonResponse` returns `totalEstimationPriceNet: 2771.90` (same as Flow 02 baseline).

### Stock vs Custom Article Distinction

| Creation Method | Upstream Endpoint | `isCustomArticle` | `articleCode` |
|-----------------|-------------------|-------------------|---------------|
| Add from catalog | `CreateOrUpdateArticleForListInventory` | `false` | Catalog code (e.g., V005) |
| Create custom | `CreateArticleFromInventory` | `true` | `9999` (custom indicator) |

Both use the same inventory line shape in `leadSurveyDto`. The middleware `PUT .../inventory/lines` route handles both — the `isCustomArticle` flag distinguishes them in responses.

### Still Missing (Do Not Invent)

1. **`CreateOrUpdateArticleForListInventory` request body** for adding stock items — only post-state inventory GET captured
2. **Fresh `CalculateEstimationPricing` request** for P1 — pack includes Flow 02 HAR reuse, not new capture
3. **Fresh `SaveEstimateWithTrueFlag` request** for P1 — pack includes stubby reused body

**Next:** Explorer to re-capture the actual stock-add POST with full request/response before claiming P1 write is fully wired. P2 (create estimate without inventory) starting next.

---

## P2–P10 (Queued)

Remain blocked on Explorer authorization. See Checklist for full queue.

---

## Timeline Notes

This plan does not estimate calendar time. Implementation involves:
- ~16 middleware routes across 4 route files (Flows 01–03)
- ~16 MCP tool definitions
- Compose and Dockerfile updates
- Documentation updates
- Test fixtures from captures

All wired captures from Flows 01–03 are implemented in this PR. P1 stock-article operations will follow in a subsequent PR once call captures land. Remaining blocked items (P2–P10) require Explorer sessions authorized by Jake.
