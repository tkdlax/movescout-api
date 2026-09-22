# Catalog capture sequence

| # | UI action | Method | Endpoint | Artifact | Result |
|---|---|---|---|---|---:|
| 1 | Inventory → Cartons room | GET | `/api/services/app/Inventory/GetAllArticlesGroupByRoomSP?leadId=1674404&estimateId=2395896&roomId=1` | `calls/001-get-all-articles-room-1/` | 16 articles |
| 2 | Inventory → Crates room | GET | same endpoint, `roomId=74` | `calls/002-get-all-articles-room-74/` | 57 articles |
| 3 | Estimate tariff chooser | GET | `/api/services/app/CustomTariffAPIService/GetCTListForEstimate?brandId=2` | `03-catalogs/calls/001-get-ct-list-for-estimate/` | 3 custom CTs |
| 4 | Estimate tariff chooser (mapped list, prior HAR) | GET | `/api/services/app/GetEstimate/GetBrandTariffMappedList` | `03-catalogs/tariff-brand-mapped.json` | 12 mapped tariffs |
| 5 | Full LOV load (prior HAR) | GET | `/api/services/app/ListOfValue/GetAllListofvalues` | `03-catalogs/lov-catalog.json` | 1,494 items / 109 tables |
| 6 | Price classes for booker 47 | POST | `/api/services/app/Alliance/ListPriceClasses?input=47` | `03-catalogs/price-class-catalog.json` | 9 |
| 7 | Move coordinators for agency 47 | GET | `/api/services/app/Dropdown/GetMoveCoordinatorListBasedOnAgencyId` | `03-catalogs/move-coordinator-catalog.json` | 45 |

Article API is room-scoped. The flat article export currently merges the two room responses captured live (73 unique room/article rows); it is not claimed as a global all-room dump.
| 8 | Inventory → PBO room | GET | same endpoint, `roomId=2` | `calls/003-get-all-articles-room-2/` | 16 articles |
| 9 | Inventory → Air room | GET | same endpoint, `roomId=71` | `calls/004-get-all-articles-room-71/` | 274 articles |
| 10 | Inventory → Barn room | GET | same endpoint, `roomId=14` | `calls/005-get-all-articles-room-14/` | 3 articles |
