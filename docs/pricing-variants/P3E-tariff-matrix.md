# P3-E Tariff Variant Matrix

**Date:** 2026-09-22  
**Estimate:** 2395896 (lead 1674404)  
**Booker:** 47 (Bailey's Moving & Storage)  
**Level:** 4 (pricingLevelId: 718)  
**Class:** Bailey's Consumer 2019 (UI selected)

## Test Matrix

`CalculateEstimationPricing` runs with different tariffs:

| tariffId | Tariff Name | totalEstimationPriceNet | HTTP | Notes |
|---:|---|---:|---|---|
| 658 | TPG | 2771.90 | 200 | Baseline |
| 660 | TPG GRR | 2771.90 | 200 | Same total as TPG |
| 659 | Allied Express | 2851.15 | 200 | +$79.25 vs TPG |
| 667 | UAS | 5115.12 | 200 | +$2343.22 vs TPG (84.5% higher) |
| 661 | 400N | — | — | Not in live selector |
| 662 | 104G | — | — | Not in live selector |
| 664 | Local/Intrastate | — | — | UI confirm cancelled; no calculate |

## Key Observations

### 1. pricingTariffId Is Authoritative

The `pricingTariffId` field determines pricing calculation. The legacy `pricingTariff` string field may lag behind — always use the ID.

### 2. Tariff Pricing Impact

| Tariff | Total | Difference from TPG |
|--------|-------|---------------------|
| TPG / TPG GRR | $2,771.90 | — |
| Allied Express | $2,851.15 | +$79.25 (+2.9%) |
| UAS | $5,115.12 | +$2,343.22 (+84.5%) |

### 3. peakOrNonPeak Flag

All captured runs had `peakOrNonPeak: false`. Peak pricing behavior not tested.

### 4. Unavailable Tariffs

- **400N (661)** and **104G (662)**: Not appearing in UI dropdown for this booker/estimate combination
- **Local/Intrastate (664)**: Selecting triggers destructive confirm dialog; UI cancel aborted capture

## Request Shape

Key tariff-related fields in `CalculateEstimationPricing` request:

```json
{
  "pricingTariffId": 658,
  "pricingTariff": "TPG",
  "peakOrNonPeak": false,
  "pricingLevelId": 718,
  "pricingLevel": "Level 4"
}
```

## Related Files

- Middleware route: `POST /leads/{id}/estimates/{eid}/calculate-pricing`
- MCP tool: `movescout_estimates_pricing_calculate`
- Upstream: `POST /api/services/app/Estimate/CalculateEstimationPricing`
