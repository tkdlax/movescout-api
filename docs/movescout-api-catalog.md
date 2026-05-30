# MoveScout Pro API Catalog (Stub)

Field lists and payload shapes for MoveScout Pro API endpoints. Expand this document with HAR captures as needed.

## Hosts

| Purpose | URL |
|---------|-----|
| Web UI (login) | `https://movescoutpro.sirva.com` |
| **API** (all REST calls) | `https://movescoutproapi.sirva.com` |

Set `MOVESCOUT_BASE_URL` to the API host. Set `MOVESCOUT_ORIGIN` to the web UI host.

## Authentication

`POST https://movescoutproapi.sirva.com/api/TokenAuth/Authenticate`

```json
{
  "userNameOrEmailAddress": "user@example.com",
  "password": "password"
}
```

Response: `{ "result": { "accessToken": "..." } }`

## Leads

### GetAllLead

`POST /api/services/app/Lead/GetAllLead`

Key request fields: `defaultFilterLead`, `filters`, `skipCount`, `maxResultCount`, `sortField`, `sortDir`

`GET /leads/page-count` (or `POST /leads/query/page-count`): probe with `maxResultCount=1`,
returns `totalCount` and `pageCount = ceil(totalCount / maxResultSize)`.

`GET /leads?page=N&maxResultSize=500`: one page only (`skipCount = (N-1) * maxResultSize`).
CSV export still auto-fetches all pages server-side.

### GetLeadById

`GET /api/services/app/Lead/GetLeadById?leadId={id}`

### CreateOrUpdateLead

`POST /api/services/app/Lead/CreateOrUpdateLead`

Minimum create fields (TBD — confirm via HAR): firstName, lastName, phone, dispositionId, tenantId, mobileSyncFlag

## Activities

### GetAllActivitiesWithCombineData

`POST /api/services/app/Activity/GetAllActivitiesWithCombineData`

### CreateOrUpdateActivity

`POST /api/services/app/Activity/CreateOrUpdateActivity`

## Filterable Lead Fields

- agencyCode
- dispositionId
- salesRepName
- creationTime
- registrationNumber
- firstName, lastName, city, state, bookerName

See [movescout-middleware-project-plan.md](../movescout-middleware-project-plan.md) for filter syntax.
