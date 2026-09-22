# Notes

- UI action: selected **Level 4** (`pricingLevelId=718`) in Pricing Info, retained TPG (`pricingTariffId=658`), existing dates/inventory, and clicked Calculate Price.
- Request `allianceDto.priceClassId`: `null`.
- Response HTTP 200, API error: `null`; actual response field is misspelled `totalEstimatinPriceNet=2771.9` (UI Grand Total `2771.90`).
- Nested `transportationSubItemCharges.totalSMFPriceNet=336.44`.
- No UpdateLeadEstimate was present in this isolated level HAR.
