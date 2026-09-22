# UI narrative — catalog exports

Session remained authenticated on estimate `2395896` / lead `1674404`.

## Inventory article picker

Opened **Inventory**, expanded multiple room sections, and observed the standard/library article picker with search field and article rows (not Custom Article). Each room expansion triggers `GetAllArticlesGroupByRoomSP` with a room id. Captured rooms 1 (Cartons), 2 (PBO), 14 (Barn), 71 (Air), and 74 (Crates), copied full responses, and merged them into `flows/03-catalogs/article-catalog.json` and `.csv` (366 rows; 363 unique article IDs). Screenshot: `screenshots/11-article-catalog-picker.webp`.

## Tariff chooser

Opened the estimate tariff dropdown. The mapped chooser list contains 12 named tariffs (TPG, Allied Express, TPG GRR, 400N, 104G, Local/Intrastate, TX Max4, UAS, ALLV-2A, CA Max4, Intra - 400N, Auto Only). Also captured `GetCTListForEstimate?brandId=2`, which returned 3 custom tariff records. Combined export: `flows/03-catalogs/tariff-catalog.json` / `.csv`. Screenshot: `screenshots/12-tariff-chooser.webp`.

## Other catalogs

The full LOV dump contains 1,494 records grouped into 109 tables and is exported as `lov-catalog.json`, `.csv`, `lov-by-table.json`, and `lov-summary.json`. Derived complete maps include 20 pricing levels (`Sirva_YM_LOV`, including id 718 Level 4), 42 valuation entries, and 11 lead-source entries. Price classes (9) and move coordinators (45) have separate flat exports.
