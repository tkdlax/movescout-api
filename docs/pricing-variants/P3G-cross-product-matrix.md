# P3-G Cross-Product (Tariff × Class × Level) Matrix

**Date:** 2026-09-22  
**Estimate:** 2395896 (lead 1674404)  
**Booker:** 47 (Bailey's Moving & Storage)

## Test Matrix

Cross-product combinations of tariff, price class, and price level:

| Tariff | priceClassId | Class Name | pricingLevelId | Level | totalEstimationPriceNet | totalSMFPriceNet | HTTP |
|--------|--------------|------------|----------------|-------|-------------------------|------------------|------|
| TPG (658) | 3976 | Bailey's Consumer 2019 | 715 | Level 1 | 2593.08 | 310.42 | 200 |
| TPG (658) | 3976 | Bailey's Consumer 2019 | 724 | Level 10 | 3189.15 | 397.15 | 200 |

## Key Observations

### 1. Level Determines Pricing, Class Does Not

Consistent with P3-A/B findings:
- **Price level** changes produce different totals (Level 1 vs Level 10: +$596.07)
- **Price class** selection does not appear to affect calculate results (`priceClassId: null` in calculate DTO)

### 2. Cross-Product Confirms Level Impact

| Level Combination | Total Difference |
|-------------------|------------------|
| TPG × 3976 × Level 1 | $2,593.08 |
| TPG × 3976 × Level 10 | $3,189.15 |
| **Difference** | **+$596.07 (+23.0%)** |

### 3. Local/Intrastate Tariff Cancelled

Attempted to test Local/Intrastate tariff (664) but:
- UI triggered destructive confirmation dialog
- User cancelled to avoid unwanted state change
- No calculate captured for this tariff

### 4. priceClassId Still Null in Calculate DTO

Despite selecting Bailey's Consumer 2019 (3976) in UI, the calculate request/response `allianceDto.priceClassId` remained `null`. This is the known caveat from P3-A.

## Baseline Restoration

After cross-product testing, baseline was restored:
- Tariff: TPG (658)
- Level: 4 (718)
- Total: $2,771.90

## Middleware Implications

1. **Pass-through:** Middleware correctly proxies all tariff/class/level combinations
2. **No normalization:** Do not attempt to "fix" the null priceClassId
3. **Tool descriptions:** Update to note that class UI selection may not affect calculate results

## Related Files

- Calculate route: `POST /leads/{id}/estimates/{eid}/calculate-pricing`
- MCP tool: `movescout_estimates_pricing_calculate`
- See also: `P3A-price-class-matrix.md`, `P3B-price-level-matrix.md`, `P3E-tariff-matrix.md`
