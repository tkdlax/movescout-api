# MoveScout Middleware API — Project Plan

**Purpose:** A hosted REST API that sits between external callers (internal tools, automations, future integrations) and the MoveScout Pro API. Each caller authenticates to the middleware with their own credentials; the middleware handles MoveScout authentication transparently on their behalf.

**Last updated:** 2026-05-28

---

## 1. Architecture Overview

```
Caller (tool / script / future app)
        │
        │  HTTP + API key or JWT
        ▼
┌─────────────────────────────────┐
│      Middleware API (ours)      │
│                                 │
│  • Route handlers               │
│  • Auth manager (token cache)   │
│  • Filter / query builder       │
│  • CSV formatter                │
└────────────┬────────────────────┘
             │  Authorization: Bearer {movescout_token}
             ▼
  MoveScout Pro API (sirva.com)
```

The middleware is stateless per request. All MoveScout state (leads, activities) lives in MoveScout. The only state the middleware holds is:
- User profiles (stored MoveScout credentials)
- Cached MoveScout access tokens (to avoid re-logging in on every call)

---

## 2. User Credential & Token Management

### Credential storage

Each middleware user has a profile record:

```
users table
─────────────────────────────────────────────
id                  UUID, primary key
name                string
api_key             string (hashed)          ← how callers authenticate to OUR API
movescout_username  string (encrypted at rest)
movescout_password  string (encrypted at rest)
created_at          datetime
```

### Token caching

MoveScout access tokens expire in 24 hours. There is no refresh endpoint — re-authentication is required at expiry. The middleware caches tokens per user to avoid authenticating on every call.

```
token_cache table (or Redis keys)
─────────────────────────────────────────────
user_id       FK → users
access_token  string
expires_at    datetime
```

**Token resolution flow (runs before every MoveScout call):**

1. Look up `token_cache` for the requesting user.
2. If a valid token exists (`expires_at > now + 5 minutes` buffer) → use it.
3. Otherwise → call `POST /api/TokenAuth/Authenticate` with stored credentials → store new token with `expires_at = now + 86400s` → use it.

> The 5-minute buffer prevents a token from expiring mid-request on long operations like large paginated exports.

### MoveScout auth headers (applied to all outbound calls)

```
Authorization: Bearer {access_token}
Content-Type: application/json-patch+json
Accept: text/plain
Origin: https://movescoutpro.sirva.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
```

---

## 3. Middleware API — Authentication

Callers authenticate to the middleware via an **API key** passed as a header:

```
X-API-Key: {api_key}
```

The middleware validates the key, resolves the user profile, and uses that profile's MoveScout credentials for downstream calls.

Future option: swap to JWT if you need scoped permissions or expiring sessions.

---

## 4. Core Endpoints to Build

### 4.1 Lead Endpoints

#### `GET /leads`
Returns a paginated list of leads. Supports filtering and sorting.

Query params:
| Param | Notes |
|---|---|
| `filter` | Base64-encoded or JSON filter spec (see Section 6) |
| `defaultFilter` | Integer 0–12 (maps to `defaultFilterLead`) — default: `3` (All Qualified) |
| `page` | Page number (1-based) |
| `pageSize` | Records per page — default 100, max 1000 |
| `sortField` | Field to sort by |
| `sortDir` | `asc` or `desc` |

Maps to: `POST /api/services/app/Lead/GetAllLead`

---

#### `GET /leads/export`
Returns a CSV file of all leads matching the given filter, paginating MoveScout automatically.

Query params: same as `GET /leads` (no `page`/`pageSize` — export fetches all pages internally).

**Pagination strategy:** Fetch in batches of 500 (safe below timeout threshold). Merge all pages, convert to CSV, stream as `Content-Disposition: attachment; filename="leads_{timestamp}.csv"`.

**CSV columns:** Derived from the `GetAllLead` response item shape. Null `*Name` fields are resolved from the LOV table (loaded once at middleware startup or cached with a short TTL). See `movescoutpro-api-catalog.md` for full field list.

Maps to: repeated `POST /api/services/app/Lead/GetAllLead` (paginated) + in-memory LOV resolution

---

#### `GET /leads/:id`
Returns a single complete lead record.

Maps to: `GET /api/services/app/Lead/GetLeadById?leadId={id}`

---

#### `POST /leads`
Creates a new lead.

Request body: lead object matching the `CreateOrUpdateLead` minimum create payload (see catalog). The middleware may provide defaults for required fields (e.g. `mobileSyncFlag: true`, `tenantId: 1`, `bookerId` from the user's agent profile).

Maps to: `POST /api/services/app/Lead/CreateOrUpdateLead`

---

#### `PUT /leads/:id`
Updates an existing lead. Caller sends only the fields to change; the middleware fetches the current lead via `GetLeadById`, merges the changes, and POSTs back the full object.

Maps to: `GET /api/services/app/Lead/GetLeadById` + `POST /api/services/app/Lead/CreateOrUpdateLead`

---

### 4.2 Survey Appointment Endpoints

#### `GET /leads/:id/appointments`
Returns all activities (survey appointments) for a lead.

Maps to: `POST /api/services/app/Activity/GetAllActivitiesWithCombineData` with `{ "leadId": "{id}" }`

---

#### `POST /leads/:id/appointments`
Creates a survey appointment for a lead.

Request body (simplified — middleware builds the full payload):
```json
{
  "surveyDate": "2026-06-15T10:00:00",
  "surveyDurationHours": 2,
  "surveyType": "onsite",
  "assigneeId": 69
}
```

The middleware:
1. Fetches the lead via `GetLeadById` (for name, address, move type)
2. Builds the `activityName` (`"{lastName}, {firstName}, {city}, {state}, {moveType}"`)
3. Builds the HTML `description` string
4. POSTs to `CreateOrUpdateActivity`
5. Calls `UpdateLeadFromAppointment` with disposition updated to Survey Scheduled
6. Returns the new activity ID

Maps to: `POST /api/services/app/Activity/CreateOrUpdateActivity` + `PUT /api/services/app/Lead/UpdateLeadFromAppointment`

---

#### `GET /appointments`
Returns activities across all leads. Supports date-range filtering.

Request params:
| Param | Notes |
|---|---|
| `startDate` | ISO 8601 — filter `activityStart >= startDate` |
| `endDate` | ISO 8601 — filter `activityStart <= endDate` |
| `type` | Activity type int (1 = survey) |
| `leadId` | Optional — scope to a single lead |

Maps to: `POST /api/services/app/Activity/GetAllActivitiesWithCombineData` with appropriate `compositeFilterDescriptorObj`

---

### 4.3 Custom / Named Query Endpoints

For bespoke queries (e.g. "booked leads for a sales rep without a reg number"), the middleware exposes a generic filter endpoint plus named shortcuts for common use cases.

#### `POST /leads/query`
Generic filter endpoint. Caller sends a filter spec; middleware maps it to the `GetAllLead` filters array format.

Request body:
```json
{
  "defaultFilter": 3,
  "filters": [
    { "field": "dispositionId",      "op": "eq",       "value": 46   },
    { "field": "salesRepName",       "op": "contains", "value": "Jacob" },
    { "field": "registrationNumber", "op": "eq",       "value": null }
  ],
  "logic": "and",
  "pageSize": 500,
  "page": 1,
  "export": false
}
```

Set `"export": true` to receive a CSV download instead of JSON.

#### Named query examples (pre-built shortcuts)

These are thin wrappers over `/leads/query` with pre-defined filter templates:

| Endpoint | Description |
|---|---|
| `GET /queries/booked-no-reg` | Booked leads missing registration number. Params: `salesRepName` (optional) |
| `GET /queries/scheduled-surveys` | Leads with survey scheduled in a date range. Params: `start`, `end` |
| `GET /queries/unassigned` | Unassigned qualified leads. |
| `GET /queries/my-leads` | All qualified leads for the requesting user's sales rep profile. |

Named queries return JSON by default; append `?format=csv` for export.

---

### 4.4 Appointment Aggregation / Deduplication

#### `GET /appointments/latest-per-lead`

Fetches all survey appointments in a given date range, deduplicates to one per lead (keeping the most recent by `activityStart`), and returns or exports the result.

Params: `startDate`, `endDate`, `format` (`json` | `csv`)

**Logic (runs in the middleware, not MoveScout):**
1. Call `GetAllActivitiesWithCombineData` with date range filter, paginated.
2. Group by `leadId`.
3. Per group, keep the record with the latest `activityStart`.
4. Return deduplicated list.

---

## 5. Filter Mapping Reference

MoveScout's `filters` array syntax (see catalog for full detail):

```json
{
  "field": "salesRepName",
  "operator": "contains",
  "value": "Jacob",
  "condition": "and",
  "date": "{current_datetime_http_format}"
}
```

The middleware populates `date` automatically with the current server time.

**Date filter value shapes:**
- Last N days: `{ "id": 6, "value": 365 }`
- Absolute range: `{ "id": 9, "value": { "start": "Jan 1, 2026", "end": "May 28, 2026" } }`

**Confirmed filterable fields:** `agencyCode`, `dispositionId`, `salesRepName`, `creationTime`, `registrationNumber` (null check). Others available — same field names as the lead object.

---

## 6. Technology Stack (Recommended)

| Layer | Recommendation | Notes |
|---|---|---|
| Runtime | **Node.js** (Express or Fastify) or **Python** (FastAPI) | FastAPI is excellent for rapid endpoint definition with auto-docs |
| Database | **PostgreSQL** | User profiles, token cache, named query definitions |
| Token cache | In-db (token_cache table) is fine for low volume; swap to **Redis** if scaling |
| Hosting | Any VPS or container (Railway, Render, Fly.io, or your own server) | Needs outbound HTTPS to sirva.com |
| Auth | **API key** for v1 (simple); JWT for v2 if you need expiring sessions |
| CSV generation | `csv-stringify` (Node) or `pandas`/`csv` (Python) | |

No exotic dependencies needed. The entire thing can be a single-service app.

---

## 7. Implementation Phases

### Phase 1 — Foundation
- [ ] User profile + credential storage (encrypted passwords)
- [ ] Token manager (auth flow, caching, auto-refresh on expiry)
- [ ] `GET /leads` — paginated list with `defaultFilter` support
- [ ] `GET /leads/:id` — single lead fetch
- [ ] `POST /leads` — create lead
- [ ] Health check / ping endpoint

### Phase 2 — Export + Updates
- [ ] `GET /leads/export` — CSV export with auto-pagination
- [ ] `PUT /leads/:id` — fetch-merge-update pattern
- [ ] `GET /leads/:id/appointments` — list lead appointments
- [ ] `POST /leads/:id/appointments` — create survey appointment

### Phase 3 — Custom Queries
- [ ] `POST /leads/query` — generic filter endpoint
- [ ] First set of named queries (booked-no-reg, unassigned, scheduled-surveys)
- [ ] `GET /appointments` — cross-lead activity search with date filter
- [ ] `GET /appointments/latest-per-lead` — deduplication endpoint

### Phase 4 — Hardening
- [ ] Request logging (per user, per endpoint)
- [ ] Error handling / MoveScout error passthrough
- [ ] Rate limiting (MoveScout has no documented limits but be conservative)
- [ ] Admin endpoint to rotate API keys
- [ ] Auto-detect token expiry failures and force re-auth

---

## 8. Key Assumptions & Open Questions

| Item | Status |
|---|---|
| MoveScout has no rate limits documented | **Assumption** — treat 1000-record pages and sequential pagination as the safe ceiling |
| No token refresh endpoint exists | **Confirmed** — re-authenticate at expiry |
| XSRF token not required for server-to-server calls | **Confirmed** — Bearer token alone works |
| `GetAllLead` page size max ~1000 | **Confirmed** — 25s at 1000; use 500 for comfortable headroom |
| `GetAllLead` returns full sub-objects (usable for CSV) | **Confirmed** — `*Name` fields are null but resolvable via LOV |
| `CreateOrUpdateLead` with `programNameId` | **Needs one more HAR** — see catalog TBD section |
| Activity date-range filter syntax | **Confirmed for GetAllLead** — same Kendo filter pattern expected on Activities but not yet HAR-captured |
| MoveScout user must have the correct agency permissions | **Assumption** — API key users must have a MoveScout account with appropriate role |

---

## 9. Security Notes

- Store MoveScout passwords **encrypted at rest** (AES-256 or equivalent). Never log them.
- API keys should be **hashed** in the database (SHA-256 or bcrypt); compare hash on inbound requests.
- All middleware traffic should be **HTTPS only**.
- Log which user hit which endpoint and when — useful for debugging and billing if you ever charge for access.
- The MoveScout `Authorization` token should never be exposed in middleware API responses.
