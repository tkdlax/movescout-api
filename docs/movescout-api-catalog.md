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

| Middleware | Upstream |
|---|---|
| `GET /leads/{id}/appointments` | `POST Activity/GetAllActivitiesWithCombineData` |
| `GET /activities/{id}` | `GET Activity/GetActivityById` |

### CreateOrUpdateActivity

`POST /api/services/app/Activity/CreateOrUpdateActivity`

| Middleware | Upstream |
|---|---|
| `POST /leads/{id}/activities` | `POST Activity/CreateOrUpdateActivity?triggerWF=true` |

### GetActivityById

`GET /api/services/app/Activity/GetActivityById?Id={activityId}`

### Move Type

| Middleware | Upstream |
|---|---|
| `GET /leads/move-type` | `GET Lead/GetMoveType` |

Query params: `originState`, `destinationState`, `originCountry`, `destinationCountry`

## List of Values

### GetAllListofvalues

`POST /api/services/app/ListOfValue/GetAllListofvalues`

`GET /lov` (cached per API user, default 24h TTL). Upstream is **GET** `ListOfValue/GetAllListofvalues` (not POST). Items use `tableName`, `id`, and `name`.

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
| `GET Dropdown/GetAllAgentList` | `GET /reference/agents` |
| `GET Dropdown/GetMoveCoordinatorListBasedOnAgencyId` | `GET /reference/move-coordinators?agencyId=` |
| `GET CustomTariffAPIService/GetCTListForEstimate` | `GET /reference/custom-tariffs?brandId=` |
| `GET LeadSourceProgram/GetPaginatedLeadSourceProgramByAgencyId` | `GET /reference/lead-source-programs?agencyId=` |

## Estimate Write Operations

| Upstream | Middleware | Notes |
|---|---|---|
| `POST Inventory/CreateOrUpdateEstimates` | `POST /leads/{id}/estimates` | Create estimate with/without inventory |
| `PUT Estimate/UpdateLeadEstimate` | `PUT /leads/{id}/estimates/{eid}` | Update tariff, pricing fields |
| `POST Estimate/CalculateEstimationPricing` | `POST .../estimates/{eid}/calculate-pricing` | Full pricing calculation |
| `GET GetEstimate/GetEstimateTariffByEffectiveDate` | `GET .../estimates/{eid}/tariff-effective` | Tariff lookup by date |

## Inventory Write Operations

| Upstream | Middleware | Notes |
|---|---|---|
| `POST Inventory/CreateOrUpdateRoom` | `POST .../estimates/{eid}/rooms` | Create/update room |
| `POST Inventory/CreateArticleFromInventory` | `POST .../rooms/{rid}/articles` | Custom article only |
| `POST Inventory/CreateOrUpdateArticleForListInventory` | `PUT .../inventory/lines` | Update line items (stock or custom) |
| `POST InventoryCommon/SaveEstimateWithTrueFlag` | `POST .../estimates/{eid}/inventory/save` | Commit changes |
| `GET Inventory/GetAllArticlesGroupByRoomSP` | `GET .../rooms/{rid}/articles` | Article catalog by room |

### Stock vs Custom Article Distinction

Both stock (catalog) and custom articles appear in `leadSurveyDto` with the same line shape. The `isCustomArticle` flag distinguishes them:

| Creation Method | Upstream Endpoint | `isCustomArticle` | `articleCode` |
|-----------------|-------------------|-------------------|---------------|
| Add from catalog | `CreateOrUpdateArticleForListInventory` | `false` | Catalog code (e.g., V005, V010) |
| Create custom | `CreateArticleFromInventory` | `true` | `9999` (custom indicator) |

**P1 examples** (estimate 2395896):
- `articleId: 870` (Air Conditioner) → `isCustomArticle: false`, `articleCode: V005` — stock
- `articleId: 874` (Armoire) → `isCustomArticle: false`, `articleCode: V010` — stock
- `articleId: 318996` (Mattress) → `isCustomArticle: true`, `articleCode: 9999` — custom

**Note:** The `CreateOrUpdateArticleForListInventory` request body for adding stock items is not yet captured. The middleware `PUT .../inventory/lines` route uses Flow 02 shapes; stock-add POST re-capture pending.

### leadSurveyDto line item fields (inventory items)

`id`, `articleId`, `articleName`, `articleCode`, `roomId`, `roomName`, `shippingQty`, `notShippingQty`, `weight`, `cube`, `shippingTotal`, `articleNotes`, `length`, `width`, `height`, `packing`, `unpacking`, `bulky`, `carton`, `pbo`, `crateFlag`, `isCustomArticle`, `make`, `year`, `model`, `segmentId`, and more — see HAR4 doc.

## Reports

### Sales performance report

Async two-step flow — generation runs in a background task (not tied to HTTP timeouts).

| Step | Method | Path | Response |
|------|--------|------|----------|
| Enqueue | POST | `/reports/sales` | **202** `{ reportId, status, expiresAt }` |
| Poll/download | GET | `/reports/sales/{reportId}` | **200** HTML file, **409** pending/running, **410** expired, **500** failed |

POST JSON body: `moveType`, `start`, `end`, `location`, `goal`, optional `salesRepName`, `defaultFilter`, optional **`callbackUrl`** (per-client webhook notified on `ready`/`failed` with **`downloadUrl`** when ready).

Requires `X-API-Key` on POST; download accepts header or `?X-API-Key=` query param for URL-based fetch (Zapier attachments). Set `API_PUBLIC_BASE_URL` for absolute `downloadUrl` values.

## Filterable Lead Fields

- agencyCode
- dispositionId
- moveTypeId
- salesRepName
- creationTime
- registrationNumber
- firstName, lastName, city, state, bookerName

See [movescout-middleware-project-plan.md](../movescout-middleware-project-plan.md) for filter syntax.
