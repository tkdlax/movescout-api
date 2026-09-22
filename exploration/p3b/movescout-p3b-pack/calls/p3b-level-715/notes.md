# Notes

- UI action: selected **Level 1** (`pricingLevelId=715`) in Pricing Info, retained TPG (`pricingTariffId=658`), existing dates/inventory, and clicked Calculate Price.
- Request `allianceDto.priceClassId`: `null`.
- Response HTTP 200, API error: `null`; actual response field is misspelled `totalEstimatinPriceNet=2593.08` (UI Grand Total `2593.08`).
- Nested `transportationSubItemCharges.totalSMFPriceNet=310.42`.
- No UpdateLeadEstimate was present in this isolated level HAR.
