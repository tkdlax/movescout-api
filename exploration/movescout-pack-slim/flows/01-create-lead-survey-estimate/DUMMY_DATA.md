# Dummy values used this run

Fill in as fields are chosen in the UI. Avoid API/test jargon in customer-facing fields.

| Field | Value | Notes |
|-------|-------|-------|
| First name | Test | |
| Last name | Lead | |
| Phone | `(415) 555-0138` | Primary type Home |
| Email | `test.lead2026@example.com` | Primary email |
| Other | Origin/destination addresses recorded below | |

## 2026-09-21 actual values

| Field | Exact value sent/used | Notes |
|---|---|---|
| First name | `Test` | Required |
| Last name | `Lead` | Required |
| Primary phone type | `Home` | Required |
| Home phone (UI) | `(415) 555-0138` | Request body serialized as `4155550138` |
| Primary email | `test.lead2026@example.com` | Required |
| Origin street | `500 North Pine Street` | UI normalized from typed `500 Pine Street` |
| Origin city/state/ZIP | `Mount Prospect`, `IL`, `60056` | UI geocoded from origin street |
| Destination street | `1250 Market Street` | Request body contained a leading space before the street |
| Destination city/state/ZIP | `San Francisco`, `CA`, `94102` | UI-derived |
| Countries | `United States` / `US` | UI default / request serialization |
| Disposition | `New` | Default |
| Shipper type | `Consumer` | Default |
| Move type | `Interstate` | Required; resolved by GetMoveType |
| Notes | blank | `leadNote: []` in request body |
| Created lead id | `1674404` | Create response result and list row |


## Survey appointment values (2026-09-21)

| Field | Value | Notes |
|---|---|---|
| Lead id | `1674404` | Qualified lead `Lead Test` |
| Appointment id | `9991980` | Created, then edited |
| Activity type | Survey Appointment | `activityType: 1` |
| Survey type | On-Site Survey | Included in description |
| Start | `09/28/2026 10:00 AM` | Sent as `2026-09-28T16:00:00.000Z` |
| End | `09/28/2026 11:00 AM` | Sent as `2026-09-28T17:00:00.000Z` |
| Assignee | Jacob Beckstead | `activityAssigneeId: 69` |
| Location | Residential / `500 North Pine Street, Mount Prospect, IL, US` | `locationType: 2` |
| Reminder (initial) | 15 Minutes Before | `reminderType: 1` |
| Reminder (modified) | 30 Minutes Before | `reminderType: 2` |

## Estimate values (2026-09-21)

| Field | Exact value observed/sent | Notes |
|---|---|---|
| Lead id | `1674404` | Qualified lead `Test Lead` |
| Estimate id | `2395868` | Existing estimate created in prior session; confirmed in editor/list and update response |
| Estimate mode | Without Inventory route | Direct editor URL used by prior exploration |
| Initial estimate name | `Lead` | Displayed before option probe |
| Revised estimate name | `Test Estimate Revised` | Only intentional option change |
| Estimate status | `Created` / `estimateStatus: 1` | List and update DTO |
| Primary | `true` | Primary Estimate checked |
| Tariff | `TPG` / `pricingTariffId: 658` | No tariff change |
| Weight / miles | `1000` / `2119` | Unchanged during probe |
| Valuation | `10000` / `ECP - $0 Ded` | Unchanged during probe |
| Update endpoint | `PUT /api/services/app/Estimate/UpdateLeadEstimate?tabSwitchFlag=false` | HTTP 200; full DTO body captured in `calls/034-UpdateLeadEstimate/` |

### Create vs option-probe update payload diff

- The initial estimate-create request was not recoverable: it occurred in the prior session, and the preserved Network buffer was empty after re-authentication. No create endpoint/body is fabricated in this record; see `calls/015-EstimateCreate-NotRecovered/`.
- The update request was captured in full. It is a full estimate DTO (20,025-byte JSON body), not a small name-only patch. Its intentional semantic change is `estimateName: "Lead"` → `"Test Estimate Revised"`; the other visible estimate options remained unchanged (TPG/658, Created/1, primary=true, weight 1000, miles 2119, valuation 10000).
- The update response returned the saved estimate with `id: 2395868`, `estimateName: "Test Estimate Revised"`, and HTTP 200. Post-save `GetAllEstimates` confirmed `totalCount: 1` for lead `1674404` and the revised name.
- HAR response bodies for most load siblings were not present in the sanitized export (only status/mime/size metadata); those folders explicitly record the response-eviction limitation. The update and post-save list response bodies were available and recorded.
