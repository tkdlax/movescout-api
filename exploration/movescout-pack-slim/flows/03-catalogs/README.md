# MoveScout catalogs (exported)

| Catalog | Count | Files | Endpoint / completeness |
|---|---:|---|---|
| Inventory articles | 3908 room/article rows (482 unique article IDs) | `article-catalog.json`, `article-catalog.csv`, `article-catalog-unique-by-id.json` | `Inventory/GetAllArticlesGroupByRoomSP`; **43/45 rooms covered**; empty: 75283; failed: 69 |
| Tariff chooser (mapped) | 12 | `tariff-brand-mapped.json`, `tariff-catalog.*` | `GetBrandTariffMappedList`; mapped chooser list captured |
| Custom tariff records | 3 | `tariff-custom-ct-list.json`, `tariff-catalog.*` | `CustomTariffAPIService/GetCTListForEstimate?brandId=2`; full response captured |
| LOV (all tables) | 1,494 / 109 tables | `lov-catalog.json`, `.csv`, `lov-by-table.json`, `lov-summary.json` | `ListOfValue/GetAllListofvalues`; full dump |
| Price levels | 20 | `price-level-catalog.*` | Derived from complete LOV table `Sirva_YM_LOV` |
| Price classes (booker 47) | 9 | `price-classes.json`, `price-class-catalog.*` | `Alliance/ListPriceClasses?input=47`; full response |
| Move coordinators (agency 47) | 45 | `move-coordinators.json`, `move-coordinator-catalog.*` | `Dropdown/GetMoveCoordinatorListBasedOnAgencyId`; full response |
| Lead source programs | 11 | `lead-source-program-catalog.*` | Derived from complete LOV table `LEAD_SOURCE` |
| Valuation types/options | 42 | `valuation-type-catalog.*` | Derived from complete valuation LOV tables |
| Density types | 49 | `density-types.json` | `Dropdown/GetListOfValuesForDensityType`; full response |
| Rooms | 45 | `rooms-for-estimate.json` | `Inventory/GetAllRoomsByDeltaForEstimate`; full response |

Raw call folders are under `03-catalogs/calls/` for the live tariff response and under `03-article-catalog/calls/` for five article-room responses. Request headers redact Authorization bearer values.


## Final article-catalog run
- Rooms covered: **43/45**
- Rows: **3908**
- Unique articleIds: **482**
- Empty rooms: 75283
- Failed rooms: 69
