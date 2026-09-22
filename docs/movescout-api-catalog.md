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

**P4 capture evidence (2026-09-22):** Full lead DTO write (not a patch-by-field API).

**Request:**
- Content-Type: `application/json-patch+json`
- Body: Full lead DTO including all nested objects

**Key fields for lifecycle updates:**
| Field | Example | Notes |
|-------|---------|-------|
| `id` | 1674404 | Lead ID (required for update) |
| `dispositionId` | 43/44 | Disposition: 43=New, 44=Pending |
| `dispositionName` | "New"/"Pending" | Display name (updated with ID) |
| `leadCustomerDetail.salesRepId` | 69/169 | Sales rep ID (triggers appointment reassignment) |
| `leadCustomerDetail.salesRepName` | "Jacob Beckstead" | Updated with salesRepId |
| `bookerId` | 47 | Booker/agency ID |
| `isQualifiedLead` | true | Qualification status |
| `qualifiedDate` | "2026-09-22T00:02:23.268-06:00" | Set when qualified |
| `leadSurveyAppointment[].activityAssigneeId` | 69/169 | Survey appointment assignee |

**Response:** ABP envelope `{ "result": <leadId>, "success": true }`

**P4 observed probes (all restored afterward):**
- Disposition change: New (43) → Pending (44) via `dispositionId`/`dispositionName`
- Sales rep change: Jacob (69) → Baylee Lopez (169) via `leadCustomerDetail.salesRepId`
- Survey appointment reassignment confirmed via `leadSurveyAppointment[0].activityAssigneeId`

**Nested DTO structure (required for updates):**
- `leadCustomerDetail` — customer/contact info, sales rep
- `leadDestination` — delivery address
- `leadMoveDate` — load/delivery dates, survey date
- `leadNonConforming` — non-conforming flags
- `leadEmployer` — employer-assisted move info
- `leadVehicle` — vehicle transport info
- `leadMoSys` — MoSys integration fields
- `leadLMP` — LMP integration fields
- `leadSurveyAppointment[]` — survey appointments
- `leadAdditionalAddress[]` — extra pickup/delivery addresses

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

### CreateOrUpdateActivity — Task Activities (P7 Documented)

`POST /api/services/app/Activity/CreateOrUpdateActivity?triggerWF=true`

**Capture source:** `flows/10-other-activities/calls/001-CreateOrUpdateActivity-Create-Task-9992843/`, `002-CreateOrUpdateActivity-Cancel-Task-9992843/`

| Middleware | Upstream |
|---|---|
| `POST /leads/{id}/activities` | `POST Activity/CreateOrUpdateActivity?triggerWF=true` |

**Activity Types:**
| activityType | Name | Notes |
|---:|---|---|
| 1 | Survey | Survey appointments (existing workflow) |
| 2 | Task | Follow-up tasks (P7 captured) |
| 3 | Event | Not captured in P7 |
| 4 | Reminder | Not captured in P7 |

**Activity Statuses:**
| activityStatus | Name |
|---:|---|
| 2 | Assigned |
| 3 | Cancelled |
| 4 | Completed |

**P7 Task Create (001 packet):**
- `activityType: 2` (Task)
- `activityStatus: 2` (Assigned)
- `reminderType: 1` (standard)
- `locationType: 2` (Residential)
- No `id` field for create; response assigns new id
- Key fields: `activityName`, `description` (HTML), `activityStart`, `activityEnd`, `activityAssigneeId`, `leadId`, `activityLocation`

**P7 Task Cancel (002 packet):**
- Same endpoint with `id: 9992843` included
- `activityStatus: 3` (Cancelled)
- Fuller DTO with timestamps: `creationTime`, `lastModificationTime`, `creatorUserId`

**Do not invent:** Event/Reminder create-reschedule operations were not captured in P7.

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

### P8 — Accessorials and Alliance Reads (2026-09-22 Capture)

**Capture source:** `flows/12-alliance-accessorials/`

#### GetEstimateAccessorialDetailsByEstimateId

`GET /api/services/app/GetEstimate/GetEstimateAccessorialDetailsByEstimateId?estimateId={id}`

| Middleware | Upstream |
|---|---|
| `GET /leads/{id}/estimates/{estimateId}/accessorials` | `GET GetEstimate/GetEstimateAccessorialDetailsByEstimateId` |

Returns the full `estimateAccessorialDto` with all accessorial configuration fields:

**Exclusive Use / Space Reservation:**
| Field | Type | Description |
|-------|------|-------------|
| `exclusiveUseOfVehicleCubicFtFlag` | bool | Enable exclusive use |
| `exclusiveUseOfVehicleCubicFeet` | number | Cubic feet for exclusive use |
| `spaceReservationCubicFtFlag` | bool | Enable space reservation |
| `spaceReservationCubicFeet` | number | Cubic feet for space reservation |
| `expeditedService` | bool | Expedited service flag |

**Shuttle Service:**
| Field | Type |
|-------|------|
| `shuttleServiceOnOffOrigin` | bool/null |
| `shuttleServiceWeightOrigin` | number/null |
| `shuttleServiceMilesOrigin` | number/null |
| `shuttleServiceOnOffDestination` | bool/null |
| (plus destination variants) | |

**Labor/Waiting Time:**
| Field | Type |
|-------|------|
| `extraLaborOriginApply` | bool |
| `originExtraLabourRate` | number/null |
| `waitingTimeOriginApply` | bool |
| `originWaitingTimeRate` | number/null |
| (plus destination and overtime variants) | |

**Stairs/Elevator/Excessive Distance:**
| Field | Type |
|-------|------|
| `isOriginStairsApply` | bool |
| `stairsWeight`, `numberOfFlights` | number/null |
| `isOriginElevatorApply` | bool |
| `isOriginExcessiveDistanceApply` | bool |
| (plus destination variants) | |

**Piano/Appliance/Rigging/Assembling:**
| Field | Type |
|-------|------|
| `isOriginPianoApply` | bool |
| `pianoType`, `numberOfPianos` | varies |
| `isOriginApplianceApply` | bool |
| `isOriginRiggingApply` | bool |
| `isOriginAssemblingApply` | bool |
| (plus destination variants) | |

#### UpdateLeadEstimate with Accessorials

`PUT /api/services/app/Estimate/UpdateLeadEstimate?tabSwitchFlag=false`

**P8 capture evidence:** `001-UpdateLeadEstimate-exclusive-use-enable/`, `002-UpdateLeadEstimate-exclusive-use-restore/`

The `estimateAccessorialDto` is nested in the full estimate DTO:

```json
{
  "id": 2395896,
  "leadId": 1674404,
  "estimateAccessorialDto": {
    "estimatesId": 2395896,
    "exclusiveUseOfVehicleCubicFtFlag": true,
    "exclusiveUseOfVehicleCubicFeet": 100,
    "expeditedService": false,
    "spaceReservationCubicFtFlag": false,
    ...
  },
  ...
}
```

**P8 observed operations:**
| Packet | exclusiveUseOfVehicleCubicFtFlag | exclusiveUseOfVehicleCubicFeet | HTTP |
|--------|----------------------------------|-------------------------------|------|
| 001-enable | `true` | 100 | 200 |
| 002-restore | `false` | 100 | 200 |

#### CalculateEstimationPricing with Accessorials

`POST /api/services/app/Estimate/CalculateEstimationPricing`

**P8 capture evidence:** `003-CalculateEstimationPricing-exclusive-use/`

The calculate endpoint accepts the same nested `estimateAccessorialDto`. In P8 testing, enabling exclusive use (100 cu ft) with the test estimate did NOT change the Grand Total ($2,771.90) or SMF ($336.44) — pricing impact depends on inventory and tariff configuration.

#### GetAllianceByLeadEstimateId

`GET /api/services/app/Alliance/GetAllianceByLeadEstimateId?Id={estimateId}`

| Middleware | Upstream |
|---|---|
| `GET /leads/{id}/estimates/{estimateId}/alliance` | `GET Alliance/GetAllianceByLeadEstimateId` |

**Response fields:**
| Field | Type | Description |
|-------|------|-------------|
| `priceClassId` | int/null | Alliance price class (often null) |
| `total` | number | Alliance total |
| `quoteId` | int | Quote identifier |
| `quoteGuid` | string/null | Quote GUID |
| `allianceEstimateNumber` | string/null | Alliance estimate number |
| `originServiceDate` | string/null | Origin service date |
| `destinationServiceDate` | string/null | Destination service date |
| `quoteRequestDate` | string/null | Quote request date |

#### GetEstimateAutoSpotDetailsByEstimateId

`GET /api/services/app/GetEstimate/GetEstimateAutoSpotDetailsByEstimateId?estimateId={id}`

| Middleware | Upstream |
|---|---|
| `GET /leads/{id}/estimates/{estimateId}/auto-spot` | `GET GetEstimate/GetEstimateAutoSpotDetailsByEstimateId` |

**Response fields:**
| Field | Type | Description |
|-------|------|-------------|
| `estimatesId` | int | Estimate ID |
| `isContractAuto` | bool/null | Contract auto flag |
| `contractChargeAmount` | number/null | Contract charge |
| `comment` | string/null | Comment |
| `estimateAutoSpotVehicles` | array | Vehicle details (empty in P8) |
| `estimateAutoSpotPriceOptions` | array | Pricing options (empty in P8) |

**P8 negative finding:** Auto Spot "Add Auto Spot" was **disabled** in the UI during capture. The vehicle and price-option arrays were empty. **Do not invent** an Auto Spot write API from this read-only capture.

#### GetEstimatePricingTotalJsonResponse

`GET /api/services/app/GetEstimate/GetEstimatePricingTotalJsonResponse?estimateId={id}`

| Middleware | Upstream |
|---|---|
| `GET /leads/{id}/estimates/{estimateId}/pricing` | `GET GetEstimate/GetEstimatePricingTotalJsonResponse` |

Returns `estimatePricingTotalDto` with `pricingResponseJson` (stringified JSON) containing detailed pricing breakdown. See P3 documentation for field details.

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
| `POST Estimate/CalculateEstimationPricing` | `POST .../estimates/{eid}/calculate-pricing` | Full pricing calculation (single/multi-segment) |
| `GET GetEstimate/GetEstimateTariffByEffectiveDate` | `GET .../estimates/{eid}/tariff-effective` | Tariff lookup by date |
| `POST Inventory/CreateOrUpdateSegments` | `POST .../estimates/{eid}/segments` | Create/update segments (P6) |
| `POST Inventory/SaveExtraPickUpAndDeliveriesForSegments` | `POST .../estimates/{eid}/extra-stops` | Save extra pickup/delivery stops (P6) |

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
| 664 | Local/Intrastate | — | UI guard blocks; see below |

**Key:** `pricingTariffId` is authoritative; legacy `pricingTariff` string may lag. All runs had `peakOrNonPeak: false`.

#### Local/Intrastate Tariff 664 — UI Guard (P3-E/P3-G)

**Capture source:** `flows/06-pricing-variants/calls/p3e-local-intrastate/`, `p3g-local-intrastate/`

Selecting **Local/Intrastate** (`pricingTariffId: 664`) in the MoveScout Pro UI triggers a destructive confirmation dialog:

> *"Are you sure? This will clear Estimate Saved Details."*

In both P3-E and P3-G captures, this confirmation was **cancelled** to avoid breaking the existing interstate inventory estimate. **No CalculateEstimationPricing request was sent** — these packets contain only meta/notes documenting the UI behavior.

**Do not assume** the API will accept an interstate estimate with `pricingTariffId: 664`. The middleware proxies whatever is sent, but the UI guards against this scenario by warning users it will clear estimate details.

This is **not an API behavior** — it's a UI safeguard that prevents sending incompatible tariff changes without explicit user confirmation.

#### P3-F — Inventory Under-Minimum (2026-09-22 Capture)

Inventory modifications on under-minimum estimates produce **flat pricing** ($2,771.90):

| Modification | APIs Called | Total |
|--------------|-------------|-------|
| Qty 2→3 (Air Conditioner 870) | `CreateOrUpdateArticleForInventory` (singular) + Calculate | 2771.90 |
| Weight/Cube 70/10→77/11 | `CreateOrUpdateArticleForInventory` (singular) + Calculate | 2771.90 |
| Carton 1.5-CP toggle | `CalculateEstimationPricing` only | 2771.90 |

All modifications restored to baseline after capture.

**Important distinction:** The qty bump and weight/cube edits use `POST Inventory/CreateOrUpdateArticleForInventory` (singular article object), **not** the batch `CreateOrUpdateArticleForListInventory` (array) endpoint. The singular endpoint is for in-place edits on existing articles without resending the full inventory state.

**Carton toggle:** The "1.5 - CP" carton checkbox toggle only triggered `CalculateEstimationPricing` with no inventory save endpoint — do not invent a separate carton API from this observation.

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
| `POST Inventory/CreateOrUpdateArticleForListInventory` | `PUT .../inventory/lines` | Update line items (stock or custom, batch) |
| `POST Inventory/CreateOrUpdateArticleForInventory` | `POST .../inventory/article` | Update single article in place |
| `POST InventoryCommon/SaveEstimateWithTrueFlag` | `POST .../estimates/{eid}/inventory/save` | Commit changes |
| `GET Inventory/GetAllArticlesGroupByRoomSP` | `GET .../rooms/{rid}/articles` | Article catalog by room |

### CreateOrUpdateArticleForListInventory — Stock Add (Flow 04 / P1 Documented)

**Capture source:** `flows/04-stock-articles-pricing/calls/07-CreateOrUpdateArticleForListInventory-stock-aircon-870/`

The request body is an **array** of inventory line items (the entire current inventory state for the estimate). Adding a stock article means updating the full array including the new item with `isQtyChange: true` for the modified row.

### CreateOrUpdateArticleForInventory — Single Article In-Place Edit (P3-F Documented)

**Capture source:** `flows/06-pricing-variants/calls/p3f-qty-bump-870/`, `p3f-weight-cube/`

`POST /api/services/app/Inventory/CreateOrUpdateArticleForInventory`

This endpoint is for **in-place edits** on a single existing inventory article (qty bump, weight/cube change). It takes a single article object (not an array). The response includes the full Calculate pricing result.

| Middleware | Upstream |
|---|---|
| `POST .../estimates/{eid}/inventory/article` | `POST Inventory/CreateOrUpdateArticleForInventory` |

**Key request fields** (from P3-F packet `p3f-qty-bump-870/request.json`):
- `estimatesId` — Estimate ID (required)
- `articleId` — Article catalog ID (required, identifies which article)
- `shippingQty` — New shipping quantity
- `weight` — Article weight (lbs)
- `cube` — Article cube (may be string or int)
- `isQtyChange` — Set to `true` when editing quantity
- `roomId`, `segmentId` — Location identifiers
- Tariff flags: `domestic`, `canada`, `maX3`, `maX4`, `grr`, `tariff400N`, `tarriff104G`, `uasFlg`, `local`, `international`
- Article flags: `carton`, `bulky`, `pbo`, `crateFlag`, `isCustomArticle`

**P3-F observed operations:**
| Modification | shippingQty | weight | cube | isQtyChange | Result |
|--------------|-------------|--------|------|-------------|--------|
| Qty bump (2→3) | 3 | 70 | 10 | true | HTTP 200, total $2,771.90 |
| Weight/cube change | 2 | 77 | "11" | true | HTTP 200, total $2,771.90 |

Note: Both operations returned identical totals because the inventory was under minimum weight threshold.

### SaveEstimateWithTrueFlag — Commit Inventory (Flow 04 / P1 Documented)

**Capture source:** `flows/04-stock-articles-pricing/calls/08-SaveEstimateWithTrueFlag-after-stock/`

Called after inventory modifications to persist changes. Query params: `estimateId`, `leadId`, `density`. Empty request body (`Content-Length: 0`). Returns `{ "result": 1, ... }` on success.

### P5 — Packing/Bulky/Crates Inventory Fields (2026-09-22 Capture)

**Capture source:** `flows/08-packing-bulky-crates/`

#### Carton Panel Toggle (001-carton-panel-existing)

Toggling carton fields (e.g., "1.5 - CP") on the estimate carton panel triggers **only** `CalculateEstimationPricing` — no separate inventory write endpoint. Grand Total stayed $2,771.90 / SMF $336.44.

#### Inventory-Line DTO Fields for Packing/Bulky/Crates

From `leadSurveyDto` items in calculate payload:

| Field | Type | Description |
|-------|------|-------------|
| `packing` | bool/null | Packing flag |
| `unpacking` | bool/null | Unpacking flag |
| `carton` | bool | Carton flag |
| `pbo` | bool | PBO (pack by owner) flag |
| `bulky` | bool | Bulky item flag |
| `bulkyWgtAdd` | bool | Bulky weight additive flag |
| `canBulky` | bool | Canadian bulky flag |
| `canBulkyWgtAdd` | bool | Canadian bulky weight additive |
| `crateFlag` | bool | Crating required flag |
| `crateType` | int | Crate type code (0=none) |
| `crateTypeId` | int/null | Crate type ID |
| `isThirdPartyCrating` | bool | Third-party crating flag |
| `isAlliance` | bool | Alliance service flag |

**Estimate-level fields:**
- `isPackingApply` — Packing services enabled
- `estimateCratesApply` — Crating services enabled

#### P5 Negative Findings — No Write APIs Observed

**Capture source:** `flows/08-packing-bulky-crates/calls/002-004` (meta only, no request/response)

The following UI controls were observed as **read-only / not exposed** on existing inventory line items:
- Pack/UnPack toggles on existing articles
- Bulky checkbox on existing articles
- 3rd Party Crate selection on existing articles

**Do not invent** separate write endpoints for these fields. The observed behavior suggests:
1. Packing/bulky/crate flags may be set only during article creation
2. Or these controls require specific inventory states not captured
3. Or line-level packing/bulky/crate edits are not supported by the API

The middleware does **not** expose Pack/UnPack/bulky/crate line-level write APIs.

### P6 — Segments and Extra Stops (2026-09-22 Capture)

**Capture source:** `flows/09-segments-extra-stops/`

#### GetSegmentsForLeadEstimate (000-load-segments)

`GET /api/services/app/GetEstimate/GetSegmentsForLeadEstimate?estimateId=2395896`

**Response:** Array of segment summaries:
```json
[
  {
    "id": 2563983,
    "name": "Segment 1",
    "pickupAddressId": 4860018,
    "deliveryAddressId": 4860019,
    "cube": 53.0,
    "weight": 371.0,
    "isDefaultSegment": true
  }
]
```

| Middleware | Upstream |
|---|---|
| `GET .../estimates/{eid}/segments` | `GET GetEstimate/GetSegmentsForLeadEstimate` |

#### CreateOrUpdateSegments (001-create-update-segments)

`POST /api/services/app/Inventory/CreateOrUpdateSegments`

**Request body:**
```json
{
  "leadId": 1674404,
  "segmentDto": [
    {
      "estimatesId": "2395896",
      "pickupAddressId": 4860018,
      "deliveryAddressId": 4860019,
      "pickupAddressName": "[main pickup]",
      "deliveryAddressName": "[main delivery]",
      "cube": 53,
      "weight": 371,
      "modeId": 192,
      "name": "Segment 1",
      "tenantId": 1,
      "pickupStopName": "MainPickup",
      "deliveryStopName": "MainDelivery",
      "id": 2563983
    },
    {
      "estimatesId": "2395896",
      "pickupAddressId": 4862738,
      "deliveryAddressId": 4860019,
      "pickupAddressName": "Will Advise",
      "deliveryAddressName": "[main delivery]",
      "cube": null,
      "weight": null,
      "modeId": 192,
      "name": "P6 Reversible Segment",
      "tenantId": 1,
      "pickupStopName": "XP1",
      "deliveryStopName": "MainDelivery",
      "id": 0
    }
  ],
  "id": 2395896
}
```

**Key fields:**
- `id: 0` in segmentDto creates a new segment; response returns assigned ID
- `modeId: 192` = Road transport mode
- `pickupStopName`/`deliveryStopName` match stop names in extra-stops array

| Middleware | Upstream |
|---|---|
| `POST .../estimates/{eid}/segments` | `POST Inventory/CreateOrUpdateSegments` |

#### SaveExtraPickUpAndDeliveriesForSegments (002-save-extra-pickup)

`POST /api/services/app/Inventory/SaveExtraPickUpAndDeliveriesForSegments`

**Request body:** Array of ALL stop addresses (main + extra):
```json
[
  {
    "leadId": 1674404,
    "estimatesId": "2395896",
    "streetAddr1": "Will Advise",
    "zip": "80202",
    "city": "Denver",
    "state": "CO",
    "country": "US",
    "addressType": 1,
    "stopName": "XP1",
    "sequenceNumber": 2,
    "isMainPickup": false,
    "isMainDelivery": false,
    "id": 4862738
  },
  {
    "leadId": 1674404,
    "estimatesId": "2395896",
    "streetAddr1": "[main pickup]",
    "zip": "60056",
    "city": "[origin city]",
    "state": "IL",
    "addressType": 1,
    "stopName": "MainPickup",
    "sequenceNumber": 1,
    "isMainPickup": true,
    "isMainDelivery": false,
    "id": 4860018
  },
  {
    "leadId": 1674404,
    "estimatesId": "2395896",
    "streetAddr1": "[main delivery]",
    "zip": "94102",
    "city": "[destination city]",
    "state": "CA",
    "addressType": 2,
    "stopName": "MainDelivery",
    "sequenceNumber": 2,
    "isMainPickup": false,
    "isMainDelivery": true,
    "id": 4860019
  }
]
```

**Key fields:**
- `addressType`: 1=pickup, 2=delivery
- `isMainPickup`/`isMainDelivery`: Identifies main origin/destination
- `id: 0` for new stops; response returns assigned address ID
- `stopName` must match segment's `pickupStopName`/`deliveryStopName`

| Middleware | Upstream |
|---|---|
| `POST .../estimates/{eid}/extra-stops` | `POST Inventory/SaveExtraPickUpAndDeliveriesForSegments` |

#### Multi-Segment Calculate (003-calculate-with-extra-stop)

`POST /api/services/app/Estimate/CalculateEstimationPricing`

With two segments and extra stop, `miles: 2201` → Grand Total $2,817.27 / SMF $342.39.
Baseline (single segment, miles 2119) → $2,771.90 / $336.44.

The calculate DTO includes full `segmentDto` array; inventory lines remain on `defaultsegmentId`.

#### Restore Path (004-restore-segment-and-stop)

Restore uses the same three endpoints:
1. `CreateOrUpdateSegments` — with only original segment
2. `SaveExtraPickUpAndDeliveriesForSegments` — with only main stops
3. `SaveEstimateWithTrueFlag` — commit changes

The `SaveEstimateWithTrueFlag` endpoint is already wired in the middleware.

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

### Basic Filter Fields
- agencyCode
- dispositionId
- moveTypeId
- salesRepName
- creationTime
- registrationNumber
- firstName, lastName, city, state, bookerName
- leadId
- activityStart, activityType

### P11 Live-Captured Filter Fields (2026-09-22)

The following filter fields were captured in live traffic and have verified wire shapes:

| UI Column | `filters[].field` | Operator | Example Value | Notes |
|-----------|-------------------|----------|---------------|-------|
| Record Id | `id` | contains | `"1675262"` | String match |
| Last Name | `leadCustomerDetail.lastName` | contains | `"Perera"` | Nested path |
| First Name | `leadCustomerDetail.firstName` | contains | `"Anoma"` | Nested path |
| Primary Email | `leadCustomerDetail.primaryEmailAddress` | contains | `"anoma@teamlassen.com"` | Nested path |
| Primary Phone Type | `leadcustomerdetail.homephone` | contains | `"Home"` | **Exact wire spelling** (lowercase, homePhone path) |
| Assigned Date | `assignedDate` | eq | `{"id": 5, "value": 30}` | Previous Month preset |

**Wire format notes:**
- Baseline (no filters): `filters: []`, `logic: ""`
- With filters: `filters: [...]`, `logic: "and"`
- Each filter object: `{field, operator, value, condition: "and", date: "<HTTP date>"}`
- Date presets use `{id, value}` objects — Previous Month = `{id: 5, value: 30}`

**Do not invent encodings** for the remaining 30+ columns in `FILTER_MAP.md`; only the six above are proven.

See [movescout-middleware-project-plan.md](../movescout-middleware-project-plan.md) for filter syntax.

## P9 — STS Registration Reads (2026-09-22)

Read-only access to STS registration data. No write APIs were captured.

### GetAllAgentSalesRepByLeadId

`GET /api/services/app/LeadEstimateSTSRegDetails/GetAllAgentSalesRepByLeadId?leadId={id}`

| Middleware | Upstream |
|---|---|
| `GET /leads/{id}/sts/agent-sales-reps` | `GET LeadEstimateSTSRegDetails/GetAllAgentSalesRepByLeadId` |

Returns array of agent sales rep records (may be empty).

### GetLeadEstimateSTSRegDetailsById

`GET /api/services/app/LeadEstimateSTSRegDetails/GetLeadEstimateSTSRegDetailsById?Id={id}`

| Middleware | Upstream |
|---|---|
| `GET /leads/{id}/sts/reg-details` | `GET LeadEstimateSTSRegDetails/GetLeadEstimateSTSRegDetailsById` |

**P9 capture:** May return 500 ABP error `"Please select originating agent on lead."` when lead lacks originating agent configuration. The middleware surfaces this as a normal upstream error.

**Do not invent** Register/STS mutate endpoints.

## P10 — Documents / Notes / Email (2026-09-22)

Observed thin GETs. No upload or email send APIs were captured.

### GetAllEstimateReportsByEstimateId

`GET /api/services/app/Report/GetAllEstimateReportsByEstimateId?estimateId={id}`

| Middleware | Upstream |
|---|---|
| `GET /leads/{id}/estimates/{estimateId}/reports` | `GET Report/GetAllEstimateReportsByEstimateId` |

Returns list of estimate reports/documents. UI shows "Documents not found" when empty. No upload control was captured.

### GetEmailTemplatesByAgencyId

`GET /api/services/app/CustomerEmailTemplate/GetEmailTemplatesByAgencyId?agencyId={id}`

| Middleware | Upstream |
|---|---|
| `GET /reference/email-templates?agencyId={id}` | `GET CustomerEmailTemplate/GetEmailTemplatesByAgencyId` |

Returns list of customer email templates for an agency. No email send API was captured (modal was canceled).

### Notes (existing endpoints)

- Lead note create/clear reuses `POST Lead/CreateOrUpdateLead` (`leadNote`/`combinedLeadNotes` fields) — already in scope
- Estimate customer-facing notes: `GET GetEstimate/GetEstimateCustomerFacingNotesByUserId?estimateId={id}` — wired at `GET /leads/{id}/estimates/{estimateId}/notes`
- Estimate note create/clear reuses `PUT Estimate/UpdateLeadEstimate` — already in scope
