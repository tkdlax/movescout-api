# Notes

- UI action: selected Bailey's Consumer 2019 (`priceClassId=3976`) and clicked the estimate-level Save button.
- The Save action caused `PUT Estimate/UpdateLeadEstimate?tabSwitchFlag=false` and returned HTTP 200.
- The retained request body is represented with the contemporaneous estimate-update body template; no secret headers are retained.
- Subsequent Calculate Price verification still showed `allianceDto.priceClassId: null` in the calculate request/response, so persistence into the pricing DTO is not proven.
