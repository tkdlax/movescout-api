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


## P3-B price-level matrix

Target estimate `2395896`; prerequisites retained: TPG (`pricingTariffId: 658`), Bailey's Consumer 2019 selected in UI, existing inventory and load/deliver dates. The API response spells the total field `totalEstimatinPriceNet`; UI Grand Total matches it.

| pricingLevelId | level | totalEstimatinPriceNet / UI Grand Total | totalSMFPriceNet | HTTP / error | packet |
|---:|---|---:|---:|---|---|
| 715 | Level 1 | 2593.08 | 310.42 | 200 / none | `calls/p3b-level-715/` |
| 718 | Level 4 (baseline controlled rerun) | 2771.90 | 336.44 | 200 / none | `calls/p3b-level-718/` |
| 724 | Level 10 | 3189.15 | 397.15 | 200 / none | `calls/p3b-level-724/` |
| 804 | Level 20 (highest available) | 4659.43 | 611.06 | 200 / none | `calls/p3b-level-804/` |

All four isolated HARs contain the calculate POST plus CORS preflight. `allianceDto.priceClassId` remained null in the level requests; see `PERSISTENCE.md` for the separate save probe.

## Dev Lead HAR ingest

P3-B HARs are staged in `calls/p3b-level-*`; the shared P3-A persistence HAR is staged in `00N-persistence-priceclass-3976/` and copied into the update packet.
