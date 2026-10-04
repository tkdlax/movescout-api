# Known / skip

Already in middleware docs — capture only if we discover different shapes:

- `POST /api/TokenAuth/Authenticate`
- `POST .../Lead/GetAllLead` (list/filter/pagination)
- `GET .../ListOfValue/GetAllListOfValues`
- Estimate/inventory **read** heroes (`GetPrimaryEstimate`, `GetEstimateByIdForInventoryTab`, pricing JSON, Alliance lists, …)
- Appointment **list** endpoints already wired in middleware (`GetAllActivitiesWithCombineData`, etc.) — **create** path is the gap

## Baseline from login probe (2026-09-21)

- Leads list reload: `POST GetAllLead` with `defaultFilterId` (not `defaultFilterLead` in live body), `maxResultCount: 12`
- LOV: `GET GetAllListOfValues` → ~1494 items
