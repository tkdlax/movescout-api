# P3-F Inventory Under-Minimum Variant Matrix

**Date:** 2026-09-22  
**Estimate:** 2395896 (lead 1674404)  
**Booker:** 47 (Bailey's Moving & Storage)  
**Tariff:** TPG (pricingTariffId: 658)  
**Level:** 4 (pricingLevelId: 718)

## Baseline

Inventory under-minimum results in flat pricing: **$2,771.90** regardless of inventory changes within the under-minimum range.

## Test Matrix

### Quantity Changes (Air Conditioner, articleId 870, room 37)

| Test | shippingQty | Weight | Cube | APIs | totalEstimationPriceNet |
|------|-------------|--------|------|------|-------------------------|
| Baseline | 2 | 70 | 10 | — | 2771.90 |
| Qty +1 | **3** | 70 | 10 | CreateOrUpdateArticleForInventory + CalculateEstimationPricing | 2771.90 |
| Restored | 2 | 70 | 10 | — | 2771.90 |

### Weight/Cube Adjustments

| Test | shippingQty | Weight | Cube | APIs | totalEstimationPriceNet |
|------|-------------|--------|------|------|-------------------------|
| Baseline | 2 | 70 | 10 | — | 2771.90 |
| Weight/Cube +10% | 2 | **77** | **11** | CreateOrUpdateArticleForInventory + CalculateEstimationPricing | 2771.90 |
| Restored | 2 | 70 | 10 | — | 2771.90 |

### Carton Toggle (1.5-CP)

| Test | Carton | APIs | totalEstimationPriceNet |
|------|--------|------|-------------------------|
| Carton ON | 1.5-CP enabled | CalculateEstimationPricing only | 2771.90 |
| Carton OFF | 1.5-CP disabled | CalculateEstimationPricing only | 2771.90 |

### Density Override

- **Skipped:** Density override test not captured in this session

## Key Observations

### 1. Under-Minimum Flat Rate

All inventory modifications within the under-minimum threshold produced **identical totals** ($2,771.90). The tariff minimum applies.

### 2. API Sequence for Inventory Changes

1. `POST CreateOrUpdateArticleForListInventory` — Updates line items (qty, weight, cube)
2. `POST CalculateEstimationPricing` — Recalculates pricing with new inventory

Carton toggle only triggers `CalculateEstimationPricing` (no inventory line update).

### 3. Inventory Restoration

All modifications were restored to baseline after capture. Final state: 2 qty, 70 lbs, 10 cu.ft.

## Middleware Impact

The middleware passes through inventory updates and pricing calculations unchanged. Under-minimum behavior is upstream logic; no special handling needed.

## Related Files

- Inventory update: `PUT /leads/{id}/estimates/{eid}/inventory/lines`
- Pricing calculate: `POST /leads/{id}/estimates/{eid}/calculate-pricing`
- MCP tools: `movescout_estimates_inventory_lines_update`, `movescout_estimates_pricing_calculate`
