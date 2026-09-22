# UI narrative — Estimate with inventory (TPG)

Status: **completed**

## Goal

Create a new estimate **with inventory** on lead `1674404` using **TPG** tariff.

## Result

- New estimate id: **2395896**
- Create path: Lead → Create estimate → With Inventory
- Tariff saved through update request as id `658` (TPG).
- Inventory committed successfully.

## Actual steps

1. Opened lead `1674404` and used the With Inventory create path.
2. Created rooms `Test Living Room` (room id `78845`) and `Test Bedroom` (room id `78846`).
3. Created custom articles Mattress (`318996`), Box (`318997`), and Chair (`318998`).
4. Saved Mattress inventory row with shipping quantity `3`; weight/cube were `0`, padding `4`.
5. Saved inventory with `SaveEstimateWithTrueFlag` (density `7`).
6. Selected tariff TPG and saved; update response confirms `pricingTariffId:658` and `isEstimateWithInventory:true`.
7. Triggered Calculate Price and queried pricing.

## Pricing blocker

`GetEstimatePricingTotalJsonResponse` returned HTTP 200 / `success:true`, but pricing totals and estimate payload were null. The UI displayed: **“Select either Price Level or Load Date to estimate”**. The visible form had empty Origin Service Date, Destination Service Date, and Price Class fields; these were not completed because the task did not provide dates/price-level values.

## Capture

Preserve log was enabled and the unsanitized HAR was exported to `network.har`. Call packets `001`–`011` contain request/response material with bearer values redacted in header files.

## Pricing completion (estimate 2395896)

The pricing blocker was resolved. In the estimate editor, selecting **BGRS - Domestic**, setting **Pricing Info Level = Level 4**, and setting the Dates section **Load From = Sep 22, 2026** and **Deliver To = Sep 29, 2026**, then clicking **Calculate Price**, produced non-null totals.

Visible totals: Transportation **$2,750.90**, Valuation **$21.00**, Grand Total **$2,771.90**. The captured `CalculateEstimationPricing` response confirms `totalEstimationPriceNet: 2771.90`, `totalSMFPriceNet: 336.44`, and `estimateNotRatedFlag: false`. Full request/response are in `calls/014-calculate-estimation-pricing/`; sanitized phase HAR is `network-pricing.har`.

The save/update calls for the prerequisite edits occurred before DevTools capture was filtered to the pricing request and are not separately packetized; the resulting values are fully present in the CalculateEstimationPricing request body.
