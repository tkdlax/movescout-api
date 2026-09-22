# P3-A Price Class Variant Matrix

**Date:** 2026-09-22  
**Estimate:** 2395896 (lead 1674404)  
**Booker:** 47 (Bailey's Moving & Storage)  
**Tariff:** TPG (pricingTariffId: 658)  
**Level:** 4 (pricingLevelId: 718)

## Test Matrix

Four `CalculateEstimationPricing` runs with different price class UI selections:

| priceClassId | Description | totalEstimationPriceNet | totalSMFPriceNet | HTTP | Error |
|---:|---|---:|---:|---|---|
| 3976 | Bailey's Consumer 2019 | 2771.90 | 336.44 | 200 | null |
| 346 | Baileys Moving & Storage | 2771.90 | 336.44 | 200 | null |
| 4235 | BGRS - Canada | 2771.90 | 336.44 | 200 | null |
| 4257 | BGRS - Domestic - General Motors | 2771.90 | 336.44 | 200 | null |

## Key Observations

1. **All totals identical:** Despite selecting four different price classes in the UI, all responses returned the same pricing totals.

2. **allianceDto.priceClassId always null:** Both request and response payloads show `allianceDto.priceClassId: null` for every run. The UI label selection is observed, but the POST payload does not carry the selected class ID.

3. **No UpdateLeadEstimate captured:** These isolated HAR captures contain only `CalculateEstimationPricing` calls. No `UpdateLeadEstimate` was observed that would persist the class selection.

## Caveat — Do Not Claim Class Persistence

The middleware `POST .../estimates/{eid}/calculate-pricing` route correctly proxies `CalculateEstimationPricing`, but:

- **Request shape:** The captured requests do not populate `allianceDto.priceClassId` with the UI-selected value
- **Class persistence:** Without an `UpdateLeadEstimate` capture, we cannot document how to persist a price class selection
- **Identical totals:** The backend may be calculating using a default or stored class, ignoring the UI picker until explicitly saved

## Next Steps

P3-B (price levels) exploration continuing. Class persistence mechanism (likely via `UpdateLeadEstimate.allianceDto.priceClassId`) needs targeted re-capture with full save flow.

## Related Files

- Middleware route: `POST /leads/{id}/estimates/{eid}/calculate-pricing`
- MCP tool: `movescout_estimates_calculate_pricing`
- Upstream: `POST /api/services/app/Estimate/CalculateEstimationPricing`
