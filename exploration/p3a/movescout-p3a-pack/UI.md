# P3-A UI narrative — price-class matrix

- Target: estimate `2395896` (lead `1674404`), booker `47`.
- Starting prerequisites retained: inventory, TPG (`pricingTariffId: 658`), Pricing Info **Level 4** (`pricingLevelId: 718`), and the existing load/deliver dates.
- For each requested class, the visible Price Class picker was changed and **Calculate Price** was clicked.
- Runs completed: Bailey's Consumer 2019 (`3976`), Baileys Moving & Storage (`346`), BGRS - Canada (`4235`), and BGRS - Domestic - General Motors (`4257`).
- No UI error text was observed.
- No field was forced to change.
- Each isolated HAR contains one successful `POST Estimate/CalculateEstimationPricing` (HTTP 200) plus its CORS preflight.
- Important fidelity note: the captured calculate payloads contain `allianceDto.priceClassId: null`, and the responses also return null for that field. The UI label selection is documented, but the POST alone does not prove that the selected class was persisted. No `UpdateLeadEstimate` appeared in these isolated HARs.
