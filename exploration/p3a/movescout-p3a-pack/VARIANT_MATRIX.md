# P3-A price-class matrix

Target estimate `2395896`; prerequisites kept at Level 4 + TPG + existing load/deliver dates. Totals below are the exact values returned by the captured `CalculateEstimationPricing` responses.

| priceClassId | description | totalEstimationPriceNet | totalSMFPriceNet | errors |
|---:|---|---:|---:|---|
| 3976 | Bailey's Consumer 2019 | 2771.9 | 336.44 | none (HTTP 200; `error: null`) |
| 346 | Baileys Moving & Storage | 2771.9 | 336.44 | none (HTTP 200; `error: null`) |
| 4235 | BGRS - Canada | 2771.9 | 336.44 | none (HTTP 200; `error: null`) |
| 4257 | BGRS - Domestic - General Motors | 2771.9 | 336.44 | none (HTTP 200; `error: null`) |

## Interpretation / limitation

All four isolated POSTs succeeded and returned identical totals. However, the observed calculate request and response have `allianceDto.priceClassId: null` for every run; no `UpdateLeadEstimate` save call was captured. Thus the table reports observed API totals without claiming that the backend applied each selected class. See each packet's `notes.md`.
