# UI narrative — Create estimate without inventory

## Goal
Create a new estimate without inventory on existing lead `1674404` (Test Lead).

## Actual click path (2026-09-22)
1. Open the lead's editable Estimates view: `https://movescoutpro.sirva.com/app/main/estimates/list/1674404`.
2. Click **Create** in the Estimates list.
3. In the **Create Estimates** modal, select **Without Inventory**.
4. Click **Create**.
5. The app navigated to `/app/main/estimates/create/false/1674404/false/false/2396567/false/false`.

## Result
- New estimate id: **2396567**.
- TPG was shown in the editor; no additional save/name change was needed to capture the create call.

## Capture
DevTools Network Preserve log was enabled and filtered to `movescoutproapi`; the successful create request was exported to `network.har`. The full JSON request is in `calls/001-create-estimate-without-inventory/request.body.json`.

## Flag observation
Although the UI path/radio was Without Inventory and the route includes `false`, the live request body had `isEstimateWithInventory: true`. Flow 02's With Inventory create also uses `true`; this discrepancy is recorded as observed rather than normalized.
