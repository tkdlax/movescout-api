# Dev Lead handoff — MoveScout exploration pack

**Source of truth:** `/workspace/movescout-exploration/`  
**Running checklist:** [`CHECKLIST.md`](./CHECKLIST.md)  
**Capture standard (Jake / CoS):** for every API call — method, URL, **all headers** (secrets redacted), request payload, response status+body, plus a supplemental UI `.md` explaining what was happening in the app when it fired.

## Open these first

1. [`CHECKLIST.md`](./CHECKLIST.md) — done vs priority queue (P1–P10); **paused until Jake says begin**
2. [`flows/01-create-lead-survey-estimate/UI.md`](./flows/01-create-lead-survey-estimate/UI.md) + [`SEQUENCE.md`](./flows/01-create-lead-survey-estimate/SEQUENCE.md) + `calls/`
3. [`flows/02-estimate-with-inventory/UI.md`](./flows/02-estimate-with-inventory/UI.md) + [`SEQUENCE.md`](./flows/02-estimate-with-inventory/SEQUENCE.md) + `calls/` + HARs
4. [`flows/03-catalogs/README.md`](./flows/03-catalogs/README.md) — LOV, tariffs, price levels/classes, articles (482 unique), rooms, etc.

## Known gaps in existing captures

| Gap | Where | Notes |
|-----|-------|-------|
| Create estimate **without inventory** request body | `flows/01-.../calls/015-EstimateCreate-NotRecovered/` | Lost after session expiry; estimate `2395868` exists |
| Many estimate **load** response bodies | Flow 01 `016`–`033` | Sanitized HAR omitted bodies; URLs/headers/meta present |
| Prerequisite UpdateLeadEstimate saves before priced calculate | Flow 02 | Values present inside `014-calculate-estimation-pricing` body; not separate folders |
| Article room SIT `69` | `flows/03-catalogs/article-response-room-69.json` | Empty/failed retrieval |
| Article room Test `75283` | same folder | API returned empty list (OK) |

## Objects in tenant (test data)

- Lead `1674404` (Test Lead)
- Appointment `9991980`
- Estimates `2395868` (no inventory), `2395896` (with inventory, TPG, priced)

## Do not start

New UI probing waits for Jake’s **begin**. This pack is for continuous consume / fold into `movescout-api` docs.
