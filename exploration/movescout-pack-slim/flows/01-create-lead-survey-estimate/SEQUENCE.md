# Call sequence — Create lead → survey appointment → estimate

Ordered list of upstream calls observed for this flow. Detail lives in `calls/NNN-Name/`.

| # | When (UI) | Method | Path | Folder | Notes |
|---|-----------|--------|------|--------|-------|

| 1 | Save/post-save | GET | `https://movescoutproapi.sirva.com//api/services/app/Lead/GetMoveType?DesinationState=CA&OriginState=IL&DesinationCountry=US&OriginCountry=US` | `calls/001-GetMoveType/` | Captured in immediate save sequence |
| 2 | Preflight | OPTIONS | `https://movescoutproapi.sirva.com//api/services/app/Lead/GetMoveType?DesinationState=CA&OriginState=IL&DesinationCountry=US&OriginCountry=US` | `calls/002-GetMoveType-Preflight/` | CORS preflight |
| 3 | Save/post-save | POST | `https://movescoutproapi.sirva.com//api/services/app/Lead/CreateOrUpdateLead` | `calls/003-CreateOrUpdateLead/` | Captured in immediate save sequence |
| 4 | Preflight | OPTIONS | `https://movescoutproapi.sirva.com//api/services/app/Lead/CreateOrUpdateLead` | `calls/004-CreateOrUpdateLead-Preflight/` | CORS preflight |
| 5 | Save/post-save | GET | `https://movescoutproapi.sirva.com//api/services/app/Lead/GetLeadById?leadId=1674404` | `calls/005-GetLeadById/` | Captured in immediate save sequence |
| 6 | Preflight | OPTIONS | `https://movescoutproapi.sirva.com//api/services/app/Lead/GetLeadById?leadId=1674404` | `calls/006-GetLeadById-Preflight/` | CORS preflight |
| 7 | Save/post-save | GET | `https://movescoutproapi.sirva.com//api/services/app/LeadSourceProgram/GetPaginatedLeadSourceProgramByAgencyId?AgencyId=47&MaxResultCount=10&SkipCount=0` | `calls/007-GetPaginatedLeadSourceProgramByAgencyId/` | Captured in immediate save sequence |
| 8 | Preflight | OPTIONS | `https://movescoutproapi.sirva.com//api/services/app/LeadSourceProgram/GetPaginatedLeadSourceProgramByAgencyId?AgencyId=47&MaxResultCount=10&SkipCount=0` | `calls/008-GetPaginatedLeadSourceProgramByAgencyId-Preflight/` | CORS preflight |

| 9 | Initial appointment save preflight | OPTIONS | `https://movescoutproapi.sirva.com//api/services/app/Activity/CreateOrUpdateActivity?triggerWF=true` | `calls/009-CreateOrUpdateActivity-Preflight-Create/` | CORS preflight; no body |
| 10 | Initial appointment save | POST | `https://movescoutproapi.sirva.com//api/services/app/Activity/CreateOrUpdateActivity?triggerWF=true` | `calls/010-CreateOrUpdateActivity-Create/` | Creates survey appointment; response status 200 |
| 11 | Modified appointment save preflight | OPTIONS | `https://movescoutproapi.sirva.com//api/services/app/Activity/CreateOrUpdateActivity?triggerWF=true` | `calls/011-CreateOrUpdateActivity-Preflight-Update/` | CORS preflight; no body |
| 12 | Modified appointment save | POST | `https://movescoutproapi.sirva.com//api/services/app/Activity/CreateOrUpdateActivity?triggerWF=true` | `calls/012-CreateOrUpdateActivity-Update/` | Updates activity 9991980; reminderType 1 → 2 |
| 13 | Appointment panel/list refresh | POST | `https://movescoutproapi.sirva.com//api/services/app/Activity/GetAllActivitiesWithCombineData` | `calls/013-GetAllActivitiesWithCombineData/` | Lead-scoped activity list; `activityType=1`, `leadId=1674404` |
| 14 | Edit appointment load | GET | `https://movescoutproapi.sirva.com//api/services/app/Activity/GetActivityById?Id=9991980` | `calls/014-GetActivityById/` | Reloads saved appointment before option edit |

## Estimate exploration (2026-09-21)

| # | When (UI) | Method | Path | Folder | Notes |
|---|-----------|--------|------|--------|-------|
| 15 | Create estimate (not recovered) | UNKNOWN | `not recoverable (prior-session create)` | `calls/015-EstimateCreate-NotRecovered/` | Prior-session creation; old Network buffer was empty after re-authentication. |
| 16 | Estimate name load | GET | `https://movescoutproapi.sirva.com//api/services/app/GetEstimate/GetEstimateName?Id=2395868` | `calls/016-GetEstimateName/` | Estimate 2395868; status 200 |
| 17 | Lead estimate load | GET | `https://movescoutproapi.sirva.com//api/services/app/GetEstimate/GetLeadEstimateById?estimateId=2395868&leadId=1674404` | `calls/017-GetLeadEstimateById/` | Lead 1674404 + estimate 2395868; status 200 |
| 18 | Brand tariff mapping | GET | `https://movescoutproapi.sirva.com//api/services/app/GetEstimate/GetBrandTariffMappedList?estimateId=2395868` | `calls/018-GetBrandTariffMappedList/` | Estimate load sibling; status 200 |
| 19 | Segments for estimate | GET | `https://movescoutproapi.sirva.com//api/services/app/GetEstimate/GetSegmentsForLeadEstimate?estimateId=2395868` | `calls/019-GetSegmentsForLeadEstimate/` | Estimate load sibling; status 200 |
| 20 | Customer-facing notes | GET | `https://movescoutproapi.sirva.com//api/services/app/GetEstimate/GetEstimateCustomerFacingNotesByUserId?estimateId=2395868` | `calls/020-GetEstimateCustomerFacingNotes/` | Estimate load sibling; status 200 |
| 21 | Service item catalog | POST | `https://movescoutproapi.sirva.com//api/services/app/Alliance/ListServiceItems` | `calls/021-ListServiceItems/` | No request body; status 200 |
| 22 | Service item types | POST | `https://movescoutproapi.sirva.com//api/services/app/Alliance/ListServiceItemsTypes` | `calls/022-ListServiceItemsTypes/` | No request body; status 200 |
| 23 | Accessorial details | GET | `https://movescoutproapi.sirva.com//api/services/app/GetEstimate/GetEstimateAccessorialDetailsByEstimateId?estimateId=2395868` | `calls/023-GetEstimateAccessorialDetails/` | Estimate load sibling; status 200 |
| 24 | Service item categories | POST | `https://movescoutproapi.sirva.com//api/services/app/Alliance/ListServiceItemCategories` | `calls/024-ListServiceItemCategories/` | No request body; status 200 |
| 25 | Booker lookup | GET | `https://movescoutproapi.sirva.com//api/services/app/Inventory/GetBookerIdOfEstimate?Id=2395868` | `calls/025-GetBookerIdOfEstimate/` | Estimate load sibling; status 200 |
| 26 | Alliance lookup | GET | `https://movescoutproapi.sirva.com//api/services/app/Alliance/GetAllianceByLeadEstimateId?Id=2395868` | `calls/026-GetAllianceByLeadEstimateId/` | Estimate load sibling; status 200 |
| 27 | Price classes | POST | `https://movescoutproapi.sirva.com//api/services/app/Alliance/ListPriceClasses?input=47` | `calls/027-ListPriceClasses/` | agency input=47; no request body; status 200 |
| 28 | Pricing total | GET | `https://movescoutproapi.sirva.com//api/services/app/GetEstimate/GetEstimatePricingTotalJsonResponse?estimateId=2395868` | `calls/028-GetEstimatePricingTotal/` | Estimate load sibling; status 200 |
| 29 | Custom tariff list | GET | `https://movescoutproapi.sirva.com//api/services/app/CustomTariffAPIService/GetCTListForEstimate?brandId=2` | `calls/029-GetCTListForEstimate/` | brandId=2; status 200 |
| 30 | Tariff effective date | GET | `https://movescoutproapi.sirva.com//api/services/app/GetEstimate/GetEstimateTariffByEffectiveDate?estimateId=2395868&tariffId=658&tariffName=TPG` | `calls/030-GetEstimateTariffByEffectiveDate/` | tariffId=658, tariffName=TPG; status 200 |
| 31 | Auto-spot details | GET | `https://movescoutproapi.sirva.com//api/services/app/GetEstimate/GetEstimateAutoSpotDetailsByEstimateId?estimateId=2395868` | `calls/031-GetEstimateAutoSpotDetails/` | Estimate load sibling; status 200 |
| 32 | Move coordinator list | GET | `https://movescoutproapi.sirva.com//api/services/app/Dropdown/GetMoveCoordinatorListBasedOnAgencyId?agencyId=47` | `calls/032-GetMoveCoordinatorList/` | agencyId=47; status 200 |
| 33 | STS registration check | POST | `https://movescoutproapi.sirva.com//api/services/app/Lead/IsLeadRegisteredToSTS` | `calls/033-IsLeadRegisteredToSTS/` | body id=1674404; status 200 |
| 34 | Option probe save | PUT | `https://movescoutproapi.sirva.com//api/services/app/Estimate/UpdateLeadEstimate?tabSwitchFlag=false` | `calls/034-UpdateLeadEstimate/` | Name changed to Test Estimate Revised; response 200 / id 2395868; status 200 |
| 35 | Post-save estimate list | POST | `https://movescoutproapi.sirva.com//api/services/app/Inventory/GetAllEstimates?leadId=1674404` | `calls/035-GetAllEstimates/` | Confirms revised name and estimate id; status 200 |
