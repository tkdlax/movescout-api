# P3-A priceClassId persistence probe

Target estimate `2395896` / lead `1674404`; tariff TPG (`658`); inventory and existing load/deliver dates retained.

## Attempts and result

1. Selected non-baseline **Bailey's Consumer 2019** (`priceClassId=3976`).
2. Explicitly clicked the estimate-level **Save** button. This produced `PUT /api/services/app/Estimate/UpdateLeadEstimate?tabSwitchFlag=false` with HTTP 200.
3. Ran Calculate Price after the save and verified the controlled Level 4 calculation.
4. The CalculateEstimationPricing request and response still contained `allianceDto.priceClassId: null`.

**Conclusion:** the UI Save endpoint fires successfully, but the selected class was not observable as a non-null `priceClassId` in the calculate DTO. Goal A remains unresolved; no class-specific persistence is claimed.

Packets: `calls/p3a-persistence-3976-update/` and `calls/p3a-persistence-3976-calculate/`.
