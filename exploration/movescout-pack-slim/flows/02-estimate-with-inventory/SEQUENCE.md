# Call sequence — Estimate with inventory (TPG)

| # | When (UI) | Method | Path | Folder | Notes |
|---|-----------|--------|------|--------|-------|
| 001 | Create estimate / With Inventory on lead 1674404 | POST | `/api/services/app/Inventory/CreateOrUpdateEstimates` | `001-create-estimate-with-inventory` | Response result `2395896`; `isEstimateWithInventory:true`. |
| 002 | Initial room creation attempt | POST | `/api/services/app/Inventory/CreateOrUpdateRoom` | `002-create-room-living-initial` | `Living Room` returned result `-1`; unique name required. |
| 003 | Add unique living room | POST | `/api/services/app/Inventory/CreateOrUpdateRoom` | `003-create-room-test-living` | `Test Living Room` → room `78845`. |
| 004 | Add bedroom | POST | `/api/services/app/Inventory/CreateOrUpdateRoom` | `004-create-room-test-bedroom` | `Test Bedroom` → room `78846`. |
| 005 | Add Mattress custom article | POST | `/api/services/app/Inventory/CreateArticleFromInventory` | `005-create-article-mattress` | Article `318996`. |
| 006 | Add Box custom article | POST | `/api/services/app/Inventory/CreateArticleFromInventory` | `006-create-article-box` | Article `318997`. |
| 007 | Add Chair custom article | POST | `/api/services/app/Inventory/CreateArticleFromInventory` | `007-create-article-chair` | Article `318998`. |
| 008 | Save inventory row | POST | `/api/services/app/Inventory/CreateOrUpdateArticleForListInventory` | `008-update-article-inventory` | Mattress qty `3`; weight/cube `0`. |
| 009 | Save inventory changes | POST | `/api/services/app/InventoryCommon/SaveEstimateWithTrueFlag?estimateId=2395896&leadId=1674404&density=7` | `009-save-estimate-inventory` | Commit succeeded. |
| 010 | Select TPG and save estimate | PUT | `/api/services/app/Estimate/UpdateLeadEstimate?tabSwitchFlag=false` | `010-update-estimate-tpg` | `pricingTariffId:658`, `isEstimateWithInventory:true`. |
| 011 | Open/calculate pricing | GET | `/api/services/app/GetEstimate/GetEstimatePricingTotalJsonResponse?estimateId=2395896` | `011-get-estimate-pricing` | Success true, totals null; UI validation says select Price Level or Load Date. |
| 012 | Load pricing options | POST | `/api/services/app/Alliance/ListPriceClasses?input=47` | `012-list-price-classes` | Returned available price classes; none was selected. |
| 013 | Resolve TPG effective tariff | GET | `/api/services/app/GetEstimate/GetEstimateTariffByEffectiveDate?estimateId=2395896&tariffId=658&tariffName=TPG` | `013-get-tpg-tariff-effective` | Returned tariff parameters (density 7, minimum weight 1000, SMF 18.6%). |
| 014 | Calculate Price after setting pricing prerequisites | POST | `/api/services/app/Estimate/CalculateEstimationPricing` | `014-calculate-estimation-pricing` | 200 OK; full 268-field request and full response captured. `totalEstimationPriceNet: 2771.90`, `totalSMFPriceNet: 336.44`, transportation 2750.90, valuation 21.00. Body includes `pricingLevel: "Level 4"`, `pricingLevelId:718`, `loadFrom:2026-09-22`, `deliverTo:2026-09-29`, `pricingTariffId:658`, `isEstimateWithInventory:true`. |
