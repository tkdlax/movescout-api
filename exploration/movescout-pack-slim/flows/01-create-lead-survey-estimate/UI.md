# UI narrative — Create lead → survey appointment → estimate

Status: **completed**

## Dummy data policy

Use ordinary-looking test data (e.g. first/last “Test” / “Lead”, normal phone/email patterns). Do **not** use names like “API Explore”, “HAR”, or “Middleware”. Prefer cancel/delete or clearly findable leads when the UI allows. Record every field we fill and any later edits used to probe options.

## Planned steps

1. From Leads list → New / Create lead
2. Fill minimum required fields with dummy data → save
3. Open the new lead → set / create a **survey appointment** (pick a future slot; change once to observe payload diffs)
4. Create an **estimate** on that lead (note wizard steps; change one option if UI exposes choices)
5. After each major save, record Network entries into `calls/NNN-*/`

## Actual steps (fill in as we go)

### 2026-09-21 — session start

- Session already signed in; target leads list: `https://movescoutpro.sirva.com/app/main/leads/list`
- Beginning create-lead UI flow; Network Preserve log on.


### 2026-09-21 — create lead completed

- Opened `https://movescoutpro.sirva.com/app/main/leads/list` in the existing signed-in session.
- Opened **Create**. DevTools Network was already open; enabled Preserve log, cleared the log, and filtered to `movescoutproapi`.
- Filled required identity/contact fields: First Name `Test`, Last Name `Lead`, Primary Phone Type `Home`, Home Phone `(415) 555-0138`, Primary Email `test.lead2026@example.com`.
- Filled required origin fields (UI geocoded/normalized): `500 North Pine Street`, `Mount Prospect`, `IL`, `60056`, United States.
- Filled required destination fields: `1250 Market Street`, `San Francisco`, `CA`, `94102`, United States.
- Defaults/required selections observed: Disposition `New`, Shipper Type `Consumer`, Move Type `Interstate`, Funded `AGT Funded`; notes remained blank.
- Clicked **Save** only; did not open survey appointment or estimate. Toast reported **Lead Created Successfully**.
- Immediate post-save Network calls included `CreateOrUpdateLead` and `GetLeadById?leadId=1674404`; list confirmation showed row `1674404 | Lead | Test`.
- Confirmed at `https://movescoutpro.sirva.com/app/main/leads/list`; lead id: `1674404`.
- From the confirmed list row, clicked **Actions → View Lead** (read-only); resulting detail URL: `https://movescoutpro.sirva.com/app/main/leads/view?id=1674404&readOnly=true`. No survey or estimate action was opened.

### 2026-09-21 — survey appointment created and modified

- Qualified lead `1674404`, opened Activities / Survey Appointments, and chose **Create** / Activity.
- Selected Activity Type **Survey Appointment** and Survey Type **On-Site Survey**.
- Associated Qualified Lead **Lead Test** (lead id `1674404`) and assigned **Jacob Beckstead**.
- Entered Location **Residential**, Reminder Type **15 Minutes Before**, Start `09/28/2026 10:00 AM`, End `09/28/2026 11:00 AM`; saved.
- Save succeeded and created appointment id `9991980`.
- Reopened appointment `9991980` with **Edit**, changed only Reminder Type from **15 Minutes Before** to **30 Minutes Before**, then saved. Toast reported **Activity Updated Successfully**.
- Network capture: initial save folders `009`–`010`; modified save folders `011`–`012`. No estimate was created.
- Related sibling calls observed around the two saves: `GetAllActivitiesWithCombineData` refreshed the lead-scoped survey list, and `GetActivityById?Id=9991980` loaded the appointment for editing.

### 2026-09-21 — estimate recovered and option probe completed

- Re-authenticated using the already populated login form; no credentials were entered. The app loaded the leads list.
- Opened DevTools Network with **Preserve log** enabled and `movescoutproapi` filter. The pre-existing buffer was empty after re-authentication, so the original estimate-creation request could not be recovered.
- Navigated directly to the editable estimate URL for lead `1674404`, estimate `2395868`, Without Inventory route. The editor loaded estimate name **Lead**, tariff **TPG**, primary estimate, status **Created**, weight `1000`, and miles `2119`.
- Captured the real estimate-load siblings (name, lead estimate, tariff mapping/effective date, segments, service items/types/categories, accessorials, pricing, booker/alliance, coordinator, and STS check) with Network Preserve log on.
- Clicked the estimate-name pencil, changed only the name from `Lead` to **Test Estimate Revised**, confirmed the inline edit, then clicked **Save**. The app returned to the estimate list and showed one Created estimate for lead `1674404` with the revised name. Toast: **Lead Estimate has been updated successfully.**
- Repeated the save with DevTools still open to capture the real update request. The successful save was `PUT /api/services/app/Estimate/UpdateLeadEstimate?tabSwitchFlag=false`; post-save list refresh was `POST /api/services/app/Inventory/GetAllEstimates?leadId=1674404`.
- Evidence: sanitized HAR `/workspace/estimate-network2.har`; call folders `015`–`035`; screenshots `06-estimate-created.webp` and `07-estimate-modified.webp`.

Status: **completed** (lead → survey appointment → estimate → estimate-name option probe). The original create request remains an explicit documented gap because its prior DevTools log was unavailable after session expiry.
