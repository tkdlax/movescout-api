# Notes

- UI action: selected **Level 10** (`pricingLevelId=724`) in Pricing Info, retained TPG (`pricingTariffId=658`), existing dates/inventory, and clicked Calculate Price.
- Request `allianceDto.priceClassId`: `null`.
- Response HTTP 200, API error: `null`; actual response field is misspelled `totalEstimatinPriceNet=3189.15` (UI Grand Total `3189.15`).
- Nested `transportationSubItemCharges.totalSMFPriceNet=397.15`.
- No UpdateLeadEstimate was present in this isolated level HAR.
