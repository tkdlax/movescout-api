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

### `isEstimateWithInventory` Flag Quirk (Flow 05 / P2 Documented)

When creating an estimate via **"Without Inventory"** in the MoveScout Pro UI:
- The UI navigates to `/create/false/...` route (the `false` indicates without inventory)
- **However**, the request body still contains `"isEstimateWithInventory": true`

**Capture source:** `flows/05-create-estimate-no-inventory/calls/001-create-estimate-without-inventory/`

This appears to be a MoveScout Pro UI/API inconsistency. The middleware **passes the flag as-is** to the upstream API without modification.

Do not attempt to "fix" or invert this flag based on UI intent — the middleware faithfully proxies the observed upstream behavior.

### CalculateEstimationPricing — Pricing Behavior (Flow 06 / P3-A/B Documented)

`POST /api/services/app/Estimate/CalculateEstimationPricing` accepts a large (~90KB) estimate body and returns pricing totals.

**Capture source:** `flows/06-pricing-variants/calls/00N-priceclass-{3976,346,4235,4257}/` (P3-A), `calls/p3b-level-{715,718,724,804}/` (P3-B)

#### P3-A Price Classes — Identical Totals

| priceClassId | totalEstimationPriceNet | totalSMFPriceNet |
|---:|---:|---:|
| 3976 | 2771.90 | 336.44 |
| 346 | 2771.90 | 336.44 |
| 4235 | 2771.90 | 336.44 |
| 4257 | 2771.90 | 336.44 |

All four price class runs returned **identical totals**. `allianceDto.priceClassId: null` in all requests/responses.

#### P3-B Price Levels — Totals DO Change

| pricingLevelId | Level | totalEstimationPriceNet | totalSMFPriceNet |
|---:|---|---:|---:|
| 715 | Level 1 | 2593.08 | 310.42 |
| 718 | Level 4 | 2771.90 | 336.44 |
| 724 | Level 10 | 3189.15 | 397.15 |
| 804 | Level 20 | 4659.43 | 611.06 |

Price levels **produce different totals** (Level 1→20: 79.7% increase).

#### API Response Field Typo

The upstream API returns both:
- `totalEstimationPriceNet` (correct spelling) — top-level in some places
- `totalEstimatinPriceNet` (typo, missing 'o') — in nested DTOs and `pricingResponseJson`

Both contain the same value. The **middleware returns the upstream response as-is** and does NOT normalize the spelling; callers must handle the misspelled field.

Key response fields:
- `result.totalEstimationPriceNet` — top-level net total (correctly spelled)
- `result.totalSMFPriceNet` — SMF total
- Inside `pricingResponseJson` (stringified JSON):
  - `totalEstimatinPriceNet` — **misspelled** net total
  - `transportationSubItemCharges.totalSMFPriceNet` — nested SMF total

#### P3-C — Load/Deliver Date Variants (2026-09-22 Capture)

**Capture source:** `flows/06-pricing-variants/calls/p3c-{load-plus30,load-plus60,short-transit,long-transit,missing-load,missing-deliver}/`

| Packet | loadFrom | deliverTo | totalEstimationPriceNet | HTTP |
|--------|----------|-----------|-------------------------|------|
| p3c-load-plus30 | 2026-10-22 | 2026-10-29 | 2771.90 | 200 |
| p3c-load-plus60 | 2026-11-21 | 2026-11-28 | 2771.90 | 200 |
| p3c-short-transit | 2026-12-01 | 2026-12-03 | 2771.90 | 200 |
| p3c-long-transit | 2026-12-01 | 2026-12-22 | 2771.90 | 200 |
| **p3c-missing-load** | **(absent)** | 2026-12-22 | 2771.90 | **200** |
| **p3c-missing-deliver** | 2026-12-01 | **(absent)** | 2771.90 | **200** |

**Key observations:**
- Totals stayed identical across all date variants (no date-based pricing adjustment observed)
- **Missing `loadFrom` or `deliverTo` still returns HTTP 200** — no validation error
- The middleware passes dates (or absence thereof) through unchanged

#### P3-D — ECP Valuation Deductibles (2026-09-22 Capture)

**Capture source:** `flows/06-pricing-variants/calls/p3d-ecp-{0,250,500}/`

| Packet | tariffValuationType | valuationTypeId | totalEstimationPriceNet |
|--------|---------------------|-----------------|-------------------------|
| p3d-ecp-0 | ECP - $0 Ded | 683 | 2771.90 |
| p3d-ecp-250 | ECP - $250 Ded | 684 | 2750.36 |
| p3d-ecp-500 | ECP - $500 Ded | 685 | 2750.36 |

Common fields: `valuationAmount=10000`, `valuationBracketId=696`

**Key observations:**
- ECP $0 Ded produces higher total than $250/$500 (valuation charge difference)
- $250 and $500 Ded produce identical totals (valuation charge = 0 for both in captured response)
- Fields `valuationTypeId` and `tariffValuationType` must match (ID takes precedence)

#### P3-E — Tariff Variants (2026-09-22 Capture)

| tariffId | Tariff Name | totalEstimationPriceNet | Notes |
|---:|---|---:|---|
| 658 | TPG | 2771.90 | Baseline |
| 660 | TPG GRR | 2771.90 | Same total as TPG |
| 659 | Allied Express | 2851.15 | +2.9% vs TPG |
| 667 | UAS | 5115.12 | +84.5% vs TPG |
| 661/662 | 400N / 104G | — | Not in live selector |
| 664 | Local/Intrastate | — | UI confirm cancelled |

**Key:** `pricingTariffId` is authoritative; legacy `pricingTariff` string may lag. All runs had `peakOrNonPeak: false`.

#### P3-F — Inventory Under-Minimum (2026-09-22 Capture)

Inventory modifications on under-minimum estimates produce **flat pricing** ($2,771.90):

| Modification | APIs Called | Total |
|--------------|-------------|-------|
| Qty 2→3 (Air Conditioner 870) | CreateOrUpdateArticleForInventory + Calculate | 2771.90 |
| Weight/Cube 70/10→77/11 | CreateOrUpdateArticleForInventory + Calculate | 2771.90 |
| Carton 1.5-CP toggle | CalculateEstimationPricing only | 2771.90 |

All modifications restored to baseline after capture.

#### P3-G — Cross-Product (Tariff × Class × Level) (2026-09-22 Capture)

| Tariff | Class (UI) | Level | totalEstimationPriceNet | totalSMFPriceNet |
|--------|------------|-------|-------------------------|------------------|
| TPG 658 | Bailey's Consumer 3976 | Level 1 (715) | 2593.08 | 310.42 |
| TPG 658 | Bailey's Consumer 3976 | Level 10 (724) | 3189.15 | 397.15 |

**Confirms:** Level determines pricing (+23% Level 1→10); class selection does not affect calculate (`priceClassId: null` in DTO).

#### Price Class Persistence — Not Confirmed (P3-A 2026-09-22 Capture)

**Capture source:** `flows/06-pricing-variants/calls/p3a-persistence-3976-{update,calculate}/`

Tested `PUT UpdateLeadEstimate?tabSwitchFlag=false` for Bailey's Consumer 2019 (`priceClassId=3976`):
- `p3a-persistence-3976-update`: HTTP 200 returned
- `p3a-persistence-3976-calculate`: Subsequent `CalculateEstimationPricing` still has `allianceDto.priceClassId: null`

**Do not claim** the middleware can persist price class selections into pricing calculations.

### UpdateLeadEstimate Request Body Shape (P3-A)

The `PUT /api/services/app/Estimate/UpdateLeadEstimate?tabSwitchFlag=false` endpoint accepts the full estimate DTO body (same shape as CalculateEstimationPricing). Key fields observed in `p3a-persistence-3976-update/request.json`:

| Field | Example | Notes |
|-------|---------|-------|
| `id` | 2395896 | Estimate ID |
| `leadId` | 1674404 | Lead ID |
| `pricingTariffId` | 658 | Tariff ID (e.g., TPG) |
| `pricingLevelId` | null | Can be null in update |
| `valuationTypeId` | 683 | ECP type ID |
| `tariffValuationType` | "ECP - $0 Ded" | ECP description |
| `valuationAmount` | 10000 | Coverage amount |
| `valuationBracketId` | 696 | Bracket ID |
| `estimateAllianceFlag` | false | Alliance pricing disabled |
| `allianceDto` | `{}` | Empty in observed update |
| `segmentDto`, `estimateSITDto`, `estimateAccessorialDto`, etc. | nested | Full nested DTOs required |

The middleware proxies this body unchanged to the upstream API.

## Inventory Write Operations

| Upstream | Middleware | Notes |
|---|---|---|
| `POST Inventory/CreateOrUpdateRoom` | `POST .../estimates/{eid}/rooms` | Create/update room |
| `POST Inventory/CreateArticleFromInventory` | `POST .../rooms/{rid}/articles` | Custom article only |
| `POST Inventory/CreateOrUpdateArticleForListInventory` | `PUT .../inventory/lines` | Update line items (stock or custom) |
| `POST InventoryCommon/SaveEstimateWithTrueFlag` | `POST .../estimates/{eid}/inventory/save` | Commit changes |
| `GET Inventory/GetAllArticlesGroupByRoomSP` | `GET .../rooms/{rid}/articles` | Article catalog by room |

### CreateOrUpdateArticleForListInventory — Stock Add (Flow 04 / P1 Documented)

**Capture source:** `flows/04-stock-articles-pricing/calls/07-CreateOrUpdateArticleForListInventory-stock-aircon-870/`

The request body is an **array** of inventory line items (the entire current inventory state for the estimate). Adding a stock article means updating the full array including the new item with `isQtyChange: true` for the modified row.

### SaveEstimateWithTrueFlag — Commit Inventory (Flow 04 / P1 Documented)

**Capture source:** `flows/04-stock-articles-pricing/calls/08-SaveEstimateWithTrueFlag-after-stock/`

Called after inventory modifications to persist changes. Query params: `estimateId`, `leadId`, `density`. Empty request body (`Content-Length: 0`). Returns `{ "result": 1, ... }` on success.

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

**P1 stock add captured:** The `CreateOrUpdateArticleForListInventory` request body for stock articles is confirmed. Key fields for stock add: `articleId` (catalog ID), `articleCode` (e.g., V005), `roomId`, `shippingQty`, `isCustomArticle: false`, `isQtyChange: true`. See fixture `tests/fixtures/stock_article_add_request.json`.

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
