# MoveScout Pro API exploration — running checklist

**Owner:** MoveScoutPro API Explorer  
**Last updated:** 2026-09-22 (America/Denver)  
**Status:** Checklist ready — **do not start next captures until Jake says begin**  
**Working root:** `/workspace/movescout-exploration/`  
**Repos:** `tkdlax/movescout-api` / live wrapper `https://mspapi.jbeckstead.com`  
**Upstream:** UI `movescoutpro.sirva.com` · API `movescoutproapi.sirva.com`

How to use this file: mark items `[x]` when done, `[~]` in progress, `[ ]` pending. After each session, update **Current position** and append a short note under **Session log**.

---

## Current position

- **In progress:** **P1** — stock (library) inventory line items + recalc pricing (Jake authorized begin 2026-09-22)
- **Session tip:** Keep UI active; always check **Remember me** on login. Prefer in-chat secure form or on-computer sign-in; bot-store secrets do not auto-fill Chrome.
- **Next after P1:** P2 — re-capture create estimate without inventory

---

## Done so far (baseline)

### Orientation
- [x] Read middleware README + OpenAPI (`mspapi.jbeckstead.com`)
- [x] Read `docs/movescout-api-catalog.md` (stub + known upstream maps)
- [x] Confirmed wrapper vs internals (auth/token cache; hero endpoints; not 1:1)

### Live session / auth notes
- [x] Login + leads list smoke (`GetAllLead`, `GetAllListOfValues`)
- [x] Documented that secure env cards store in bot secret store but do **not** inject into browser/env for GUI login
- [x] Standing preference: select **Remember me** on MoveScout login

### Flow 01 — Create lead → survey → estimate (without inventory)
Path: `flows/01-create-lead-survey-estimate/`

- [x] Create lead `1674404` (Test Lead) + capture `CreateOrUpdateLead` / `GetMoveType` / `GetLeadById`
- [x] Survey appointment `9991980` + option probe (`reminderType` 1→2) via `CreateOrUpdateActivity`
- [x] Estimate `2395868` Without Inventory; load constellation; name update via `PUT Estimate/UpdateLeadEstimate`
- [ ] **GAP:** original **create estimate (without inventory)** request body lost after session expiry (`calls/015-EstimateCreate-NotRecovered`)

### Flow 02 — Estimate with inventory (TPG) + pricing
Path: `flows/02-estimate-with-inventory/`

- [x] Create with inventory: `POST Inventory/CreateOrUpdateEstimates` → estimate `2395896`
- [x] Rooms: `CreateOrUpdateRoom` (unique names) → `78845` / `78846`
- [x] Custom articles: `CreateArticleFromInventory` → Mattress/Box/Chair ids
- [x] Line save: `CreateOrUpdateArticleForListInventory` + `SaveEstimateWithTrueFlag`
- [x] Tariff TPG (`pricingTariffId` 658) via `UpdateLeadEstimate`
- [x] Pricing blocker documented (null totals until Price Level / Load Date)
- [x] Priced run: Price Class BGRS Domestic + Level 4 + dates → `POST Estimate/CalculateEstimationPricing` (Grand Total $2,771.90)
- [x] HAR exports (`network.har`, `network-pricing.har`)

### Flow 03 — Catalogs
Path: `flows/03-catalogs/` (+ article HAR under `flows/03-article-catalog/`)

- [x] LOV full dump (1,494 items / 109 tables)
- [x] Tariffs (brand-mapped 12 + CT list → 15 in tariff-catalog)
- [x] Price levels (20 from `Sirva_YM_LOV`)
- [x] Price classes booker 47 (9)
- [x] Move coordinators agency 47 (45)
- [x] Density types (49)
- [x] Rooms library (45) via `GetAllRoomsByDeltaForEstimate`
- [x] Valuation / lead source catalogs derived from LOV
- [x] Article library via `GetAllArticlesGroupByRoomSP` — **3,908 rows / 482 unique ids / 43 of 45 rooms** (empty: Test `75283`; failed: SIT `69`)
- [x] `article-catalog.json` / `.csv` / `article-catalog-unique-by-id.json`

---

## Priority queue (attack when Jake says begin)

Mark progress here; expand large items into sub-checklists below.

- [~] **P1 — Stock (library) inventory line items**  
  Add catalog `articleId`s (not customs) to rooms; capture qty/weight/cube payloads; contrast with `CreateArticleFromInventory`. Recalc pricing after.
- [ ] **P2 — Re-capture create estimate without inventory**  
  Close Flow 01 gap: full create request/response body for Without Inventory path.
- [ ] **P3 — Pricing variants (LARGE)** — see detailed checklist below  
  Systematically probe price class, level, dates, valuation, tariff, inventory weight/qty; document how `CalculateEstimationPricing` request/response fields change.
- [ ] **P4 — Lead lifecycle updates**  
  Disposition / qualify / sales rep / booker updates via UI → `CreateOrUpdateLead` update payloads.
- [ ] **P5 — Packing, cartons, bulky, crates**  
  Toggle packing/unpacking, carton/PBO, bulky, crate on line items; capture inventory + pricing impact.
- [ ] **P6 — Segments & extra stops**  
  Extra stop rooms / segment edits; impact on estimate DTO and pricing.
- [ ] **P7 — Other activity types**  
  Phone/virtual survey, follow-ups, cancel/reschedule (`CreateOrUpdateActivity`).
- [ ] **P8 — Alliance / accessorials / auto-spot writes**  
  Move beyond reads; capture create/update endpoints if used in UI.
- [ ] **P9 — Registration / STS**  
  Document real register / STS flows beyond `IsLeadRegisteredToSTS`.
- [ ] **P10 — Documents, notes, emails**  
  Lead notes, customer-facing estimate notes, doc upload/send.

### Later / hygiene
- [ ] Retry SIT room `69` article dump if needed
- [ ] Fold proven mappings into `tkdlax/movescout-api` `docs/movescout-api-catalog.md` (+ OpenAPI where appropriate)
- [ ] Optional: export checklist + catalogs into the git repo via Cursor cloud agent when Jake wants commits

---

## P3 — Pricing variants (large task)

Treat each row as its own capture packet under e.g. `flows/04-pricing-variants/`. Keep Network Preserve log; export HAR per variant group. Always note prerequisites (tariff, price class, level, loadFrom, deliverTo, valuation).

### Baseline (already done — reference only)
- [x] TPG + BGRS Domestic + Level 4 + load/deliver dates on estimate `2395896` → `$2,771.90`

### A. Price class matrix (booker 47 classes from catalog)
- [ ] Bailey's Consumer 2019 (`3976`)
- [ ] Baileys Moving & Storage (`346`)
- [ ] BGRS - Canada (`4235`)
- [ ] BGRS - Domestic (`4231`) — baseline exists; re-run only if needed for controlled diffs
- [ ] BGRS - Domestic - General Motors (`4257`)
- [ ] Military - DP3 Non-Peak (`3871`)
- [ ] Military - DP3 Peak (`3868`)
- [ ] SIRVA - International (`2705`)
- [ ] SIRVA Relo. - Enterprise (`2684`)
- [ ] Document which classes error / require extra fields / refuse TPG

### B. Price level sweep (`Sirva_YM_LOV` — 20 levels)
- [ ] Level 1 (`715`) … through Level set — at minimum sample **low / mid / high** (e.g. 1, 4, 10, max) if full 20 is too costly; prefer full sweep when session is stable
- [ ] Record `pricingLevel` / `pricingLevelId` vs `totalEstimationPriceNet` / SMF

### C. Load / deliver date variants
- [ ] Peak vs non-peak windows (if detectable via `peakOrNonPeak` or tariff effective dates)
- [ ] Same-week vs +30/+60 day load
- [ ] Deliver spread (short vs long transit)
- [ ] Missing load vs missing deliver (confirm validation messages / null pricing)

### D. Valuation types (from LOV valuation catalogs)
- [ ] ECP $0 / $250 / $500 Ded (and other deductibles as applicable)
- [ ] Actual Cash Value / Declared Value
- [ ] Bracket changes where UI allows
- [ ] Diff `CalculateEstimationPricing` valuation section + UI Grand Total

### E. Tariff variants (from tariff-catalog — 15)
- [ ] TPG (baseline)
- [ ] TPG GRR
- [ ] Allied Express
- [ ] 400N / Intra-400N
- [ ] 104G
- [ ] Local/Intrastate (+ NSL/CO/GJ CT locals if selectable)
- [ ] TX Max4 / CA Max4
- [ ] UAS / ALLV-2A / Auto Only
- [ ] Note which tariffs need different move type / states

### F. Inventory-driven pricing
- [ ] Increase shipping qty on stock article → recalc
- [ ] Non-zero weight/cube vs zero-weight customs
- [ ] Add bulky / carton lines → recalc
- [ ] Density override if UI exposes it

### G. Cross-product spot checks (only after A–F samples exist)
- [ ] One Interstate TPG × Bailey's Consumer × Level 1
- [ ] One Interstate TPG × Bailey's Consumer × Level 10
- [ ] One Local/Intrastate tariff × matching price class (if applicable)

**P3 definition of done:** Variant matrix spreadsheet or markdown table of inputs → `totalEstimationPriceNet` / key response fields, plus call folders for each successful calculate; failed combinations documented with UI/API errors.

---

## Session log

| When (PT) | Note |
|-----------|------|
| 2026-09-21 | Flows 01–02; catalogs started; estimate create-without-inventory body lost |
| 2026-09-22 | Catalogs expanded; full article dump 482 unique / 43 rooms; CoS report + this checklist created; **awaiting begin** |
| 2026-09-22 | CoS capture standard locked; HANDOFF.md for Dev Lead; still awaiting Jake begin |
| 2026-09-22 | Jake: confirm CoS handoff then begin; started P1 stock library articles |
