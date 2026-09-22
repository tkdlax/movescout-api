# Call sequence — Create estimate without inventory

| # | UI action | Method | Path | Folder | Notes |
|---|---|---|---|---|---|
| 001 | Lead 1674404 → Estimates → Create → Without Inventory | POST | `/api/services/app/Inventory/CreateOrUpdateEstimates` | `calls/001-create-estimate-without-inventory` | 200 OK; response result `2396567`; route `/create/false/...`; observed body flag `isEstimateWithInventory:true`. |

The request/response were captured from the sanitized HAR export.
