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

## List of Values

### GetAllListofvalues

`POST /api/services/app/ListOfValue/GetAllListofvalues`

Middleware: `GET /lov` (cached per API user, default 24h TTL).

## Inventory and Estimates (HAR4)

### Hero endpoint

`GET /leads/{leadId}/inventory` — resolves primary estimate, loads `GetEstimateByIdForInventoryTab`, groups `leadSurveyDto` by room.

Query params: `estimateId`, `includeSummary` (default true), `shippingOnly` (default false).

Internal sequence:
1. `GET Estimate/GetPrimaryEstimate?id={leadId}` (skipped if `estimateId` provided)
2. `GET Inventory/GetEstimateByIdForInventoryTab?estimateId={id}`
3. `GET Inventory/GetEstimateSummary?estimateId={id}` (optional)

### Lead pricing (one call)

`GET /leads/{leadId}/pricing` — resolves primary estimate, calls `GetEstimatePricingTotalJsonResponse`.

Query params: `estimateId` (optional override). Returns `leadId`, `estimateId`, `estimateName`, plus MoveScout pricing fields.

### Inventory service

| Upstream | Middleware |
|---|---|
| `POST Inventory/GetAllEstimates?leadId=` | `GET /leads/{id}/estimates` |
| `GET Estimate/GetPrimaryEstimate` | `GET /leads/{id}/estimates/primary` |
| `GET Inventory/GetEstimateByIdForInventoryTab` | `GET /leads/{id}/estimates/{estimateId}` |
| `GET Inventory/GetEstimateSummary` | `GET /leads/{id}/estimates/{estimateId}/summary` |
| `GET Inventory/GetAllRoomsByDeltaForEstimate` | `GET /leads/{id}/estimates/{estimateId}/rooms` |
| `GET Inventory/GetBookerIdOfEstimate` | `GET /leads/{id}/estimates/{estimateId}/booker-id` |

### GetEstimate service

| Upstream | Middleware |
|---|---|
| `GET GetEstimate/GetSegmentsForLeadEstimate` | `.../segments` |
| `GET GetEstimate/GetEstimateAccessorialDetailsByEstimateId` | `.../accessorials` |
| `GET GetEstimate/GetEstimatePricingTotalJsonResponse` | `.../pricing` |
| `GET GetEstimate/GetBrandTariffMappedList` | `.../tariffs` |
| `GET GetEstimate/GetEstimateAutoSpotDetailsByEstimateId` | `.../auto-spot` |
| `GET GetEstimate/GetEstimateCustomerFacingNotesByUserId` | `.../notes` |

### Alliance reference data

| Upstream | Middleware |
|---|---|
| `POST Alliance/ListServiceItems` | `GET /reference/service-items` |
| `POST Alliance/ListServiceItemsTypes` | `GET /reference/service-item-types` |
| `POST Alliance/ListServiceItemCategories` | `GET /reference/service-item-categories` |
| `POST Alliance/ListPriceClasses?input=` | `GET /reference/price-classes?bookerId=` |
| `GET Alliance/GetAllianceByLeadEstimateId` | `GET /leads/{id}/estimates/{estimateId}/alliance` |

### Other reference data

| Upstream | Middleware |
|---|---|
| `GET AutoMakeModel/GetAllMakeModelDetails` | `GET /reference/vehicles` |
| `GET TransitGuideSeasonConfiguration/GetAllTransitGuideSeasonConfiguration` | `GET /reference/transit-seasons` |

### leadSurveyDto line item fields (inventory items)

`id`, `articleId`, `articleName`, `articleCode`, `roomId`, `roomName`, `shippingQty`, `notShippingQty`, `weight`, `cube`, `shippingTotal`, `articleNotes`, `length`, `width`, `height`, `packing`, `unpacking`, `bulky`, `carton`, `pbo`, `crateFlag`, `isCustomArticle`, `make`, `year`, `model`, `segmentId`, and more — see HAR4 doc.

## Reports

### Sales performance report

Async two-step flow — generation runs in a background task (not tied to HTTP timeouts).

| Step | Method | Path | Response |
|------|--------|------|----------|
| Enqueue | POST | `/reports/sales` | **202** `{ reportId, status, expiresAt }` |
| Poll/download | GET | `/reports/sales/{reportId}` | **200** HTML file, **409** pending/running, **410** expired, **500** failed |

Query params (POST): same as before — `move_type`, `start`, `end`, `location`, `goal`, optional `salesRepName`, `defaultFilter`.

Requires `X-API-Key` on both calls. Job metadata in Postgres (`report_jobs` table); HTML on disk until `REPORT_TTL_SECONDS` (default 1h). Deploy: `alembic upgrade head`.

Optional env: `REPORT_MAX_LEADS`, `REPORT_STORAGE_DIR`, `REPORT_TTL_SECONDS`, `REPORT_SWEEP_INTERVAL_SECONDS`.

## Filterable Lead Fields

- agencyCode
- dispositionId
- moveTypeId
- salesRepName
- creationTime
- registrationNumber
- firstName, lastName, city, state, bookerName

See [movescout-middleware-project-plan.md](../movescout-middleware-project-plan.md) for filter syntax.
