# Notes

Pricing prerequisites were set before calculation:
- Price Class selected in the UI: **BGRS - Domestic**
- Pricing Info Level: **Level 4** (`pricingLevelId: 718` in the captured body)
- Load From: **2026-09-22** (`2026-09-22T00:00:00.000Z`)
- Deliver To: **2026-09-29** (`2026-09-29T00:00:00.000Z`)

The calculation succeeded (`success: true`). The full response is saved in `response.json`; its top-level `result` reports:
- `totalEstimationPriceNet`: **2771.90**
- `totalSMFPriceNet`: **336.44**
- `netPackPriceAmount`: **0.00**
- `estimateNotRatedFlag`: **false**

The embedded `pricingResponseJson` reports:
- Transportation net: **2750.90**
- Valuation net: **21.00**
- Total estimating price net: **2771.90**
- Total weight: **1000.0**
- SMF percentage: **18.6**

The UI matched these values: Transportation $2,750.90; Valuation $21.00; Grand Total $2,771.90. The earlier “Select either Price Level or Load Date to estimate” blocker was cleared by the load/delivery dates and pricing level.
