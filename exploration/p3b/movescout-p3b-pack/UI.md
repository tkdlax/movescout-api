# P3-A UI narrative — price-class matrix

- Target: estimate `2395896` (lead `1674404`), booker `47`.
- Starting prerequisites retained: inventory, TPG (`pricingTariffId: 658`), Pricing Info **Level 4** (`pricingLevelId: 718`), and the existing load/deliver dates.
- For each requested class, the visible Price Class picker was changed and **Calculate Price** was clicked.
- Runs completed: Bailey's Consumer 2019 (`3976`), Baileys Moving & Storage (`346`), BGRS - Canada (`4235`), and BGRS - Domestic - General Motors (`4257`).
- No UI error text was observed.
- No field was forced to change.
- Each isolated HAR contains one successful `POST Estimate/CalculateEstimationPricing` (HTTP 200) plus its CORS preflight.
- Important fidelity note: the captured calculate payloads contain `allianceDto.priceClassId: null`, and the responses also return null for that field. The UI label selection is documented, but the POST alone does not prove that the selected class was persisted. No `UpdateLeadEstimate` appeared in these isolated HARs.


## P3-B price-level sweep

- Same estimate `2395896`, TPG, inventory, and dates were retained. The visible Pricing Info **Level** picker accepted Level 1 (`715`), Level 4 (`718`), Level 10 (`724`), and Level 20 (`804`, highest catalog level).
- Each run used a clear/filter Network log and **Calculate Price**; no article chooser or room-wide article fetch was opened.
- UI totals after calculation: Level 1 `$2,593.08` / SMF flat `$310.42`; Level 4 `$2,771.90` / `$336.44`; Level 10 `$3,189.15` / `$397.15`; Level 20 `$4,659.43` / `$611.06`.
- Each calculate returned HTTP 200 with no API error.
