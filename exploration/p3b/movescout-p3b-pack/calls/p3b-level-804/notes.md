# Notes

- UI action: selected **Level 20 (maximum)** (`pricingLevelId=804`) in Pricing Info, retained TPG (`pricingTariffId=658`), existing dates/inventory, and clicked Calculate Price.
- Request `allianceDto.priceClassId`: `null`.
- Response HTTP 200, API error: `null`; actual response field is misspelled `totalEstimatinPriceNet=4659.43` (UI Grand Total `4659.43`).
- Nested `transportationSubItemCharges.totalSMFPriceNet=611.06`.
- No UpdateLeadEstimate was present in this isolated level HAR.
