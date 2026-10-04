# Call sequence — P1 Stock articles + pricing

| # | When (UI) | Method | Path | Folder | Notes |
|---|-----------|--------|------|--------|-------|
| 1 | After adding stock items | GET | `Inventory/GetEstimateByIdForInventoryTab?estimateId=2395896` | `network.har` | `leadSurveyDto` includes 870/874/879 + custom mattress 318996 |
| 2 | Pricing tab | GET | `GetEstimate/GetEstimatePricingTotalJsonResponse` | `network.har` | |
| 3 | Estimate load | GET | `GetEstimate/GetLeadEstimateById` | `network.har` | |
| 4 | Tariff | GET | `GetEstimate/GetEstimateTariffByEffectiveDate` | `network.har` | TPG |
| 5 | Inventory save | POST | `Inventory/SaveEstimateDataToTempTableWithBackgroundJob` | `network.har` | |
| 6 | Calculate Price | POST | `Estimate/CalculateEstimationPricing` | `network.har` | Total still 2771.90 |

**Not in HAR:** the actual add-article POST for stock ids (documented gap).
