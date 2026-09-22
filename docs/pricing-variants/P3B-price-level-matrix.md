# P3-B Price Level Variant Matrix

**Date:** 2026-09-22  
**Estimate:** 2395896 (lead 1674404)  
**Booker:** 47 (Bailey's Moving & Storage)  
**Tariff:** TPG (pricingTariffId: 658)  
**Class:** Bailey's Consumer 2019 (selected in UI)

## Test Matrix

Four `CalculateEstimationPricing` runs with different price levels:

| pricingLevelId | Level | totalEstimationPriceNet | totalSMFPriceNet | HTTP | Error |
|---:|---|---:|---:|---|---|
| 715 | Level 1 | 2593.08 | 310.42 | 200 | null |
| 718 | Level 4 (baseline) | 2771.90 | 336.44 | 200 | null |
| 724 | Level 10 | 3189.15 | 397.15 | 200 | null |
| 804 | Level 20 (highest) | 4659.43 | 611.06 | 200 | null |

## Key Observations

### 1. Levels DO Change Totals

Unlike price classes (P3-A), price levels **do produce different totals**:
- Level 1 → Level 20 range: $2,593.08 → $4,659.43 (79.7% increase)
- SMF range: $310.42 → $611.06

### 2. API Response Field Typo

The upstream API response contains both:
- `totalEstimationPriceNet` (correct spelling) — top-level result
- `totalEstimatinPriceNet` (typo, missing 'o') — nested in some DTO structures

Both fields contain the same value. The middleware returns the top-level `totalEstimationPriceNet`.

### 3. priceClassId Still Null

Even with different levels, `allianceDto.priceClassId` remained `null` in all calculate requests/responses.

## Persistence Probe Results

Tested `UpdateLeadEstimate` for price class persistence:

1. Selected Bailey's Consumer 2019 (`priceClassId=3976`) in UI
2. Clicked estimate-level **Save** button
3. `PUT /api/services/app/Estimate/UpdateLeadEstimate?tabSwitchFlag=false` → HTTP 200
4. Ran `CalculateEstimationPricing` after save
5. **Result:** Calculate request/response still showed `allianceDto.priceClassId: null`

**Conclusion:** The UI save endpoint fires successfully, but the selected class is not reflected in the calculate DTO. Price class persistence mechanism remains unconfirmed.

## Related Files

- Middleware route: `POST /leads/{id}/estimates/{eid}/calculate-pricing`
- MCP tool: `movescout_estimates_calculate_pricing`
- Upstream: `POST /api/services/app/Estimate/CalculateEstimationPricing`
- Update route: `PUT /leads/{id}/estimates/{eid}` (UpdateLeadEstimate)

## Next Steps

- P3-C: Load/deliver date variants (queued)
- Price class persistence: Needs deeper investigation into `UpdateLeadEstimate` body fields
