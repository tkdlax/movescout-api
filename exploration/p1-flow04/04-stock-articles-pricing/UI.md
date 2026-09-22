# UI narrative — P1 Stock (library) articles + pricing recalc

Status: **completed (HAR incomplete on add-POST bodies)**

## Goal

On estimate `2395896` (lead `1674404`, TPG), add **library/catalog** articles by existing `articleId` (not `CreateArticleFromInventory` customs). Capture payloads, then recalculate pricing.

## Actual steps (2026-09-22)

- Signed in with **Remember me**.
- Opened with-inventory estimate `2395896` inventory UI.
- Added stock catalog articles (one at a time; no bulk room-article dump):
  - `870` Air Conditioner (`V005`) → Living Room `37`, qty 1, weight 70, cube 10, `isCustomArticle: false`
  - `874` Armoire (`V010`) → Master Bedroom `39`, qty 1, weight 210, cube 30, `isCustomArticle: false`
  - `879` Bar, Stool (`V015`) → Bedroom 2 `27`, qty 1, weight 21, cube 3, `isCustomArticle: true` in subsequent GET (unexpected vs 870/874)
- Recalculated price: Grand Total still **$2,771.90** (tariff min weight 1000 still on estimate).
- Evidence: `network.har` (6 entries) includes `GetEstimateByIdForInventoryTab` with `leadSurveyDto` listing the new lines, plus `CalculateEstimationPricing`.
- **Gap:** add-to-inventory POST bodies (`CreateOrUpdateArticleForListInventory` or equivalent) were not preserved in this HAR. Contrast vs customs still visible: stock lines use catalog `articleId`/`articleCode` and weight/cube from library.

## Contrast vs custom path

Custom path: `POST Inventory/CreateArticleFromInventory` (name → new tenant articleId) then `CreateOrUpdateArticleForListInventory` with `isCustomArticle: true`.
Stock path: reuse catalog ids 870/874/879; GET inventory tab shows `isCustomArticle: false` for A/C and Armoire.
