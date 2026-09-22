# P3-A sequence — price-class matrix

1. Open estimate `2395896` in the Estimates editor.
2. Preserve inventory, TPG, Level 4, and existing load/deliver dates.
3. Select one Price Class in the picker.
4. Clear/ isolate the Network log.
5. Click **Calculate Price** and wait for the totals to refresh.
6. Export the HAR to that class folder.
7. Repeat for the next class.

| Run | Class ID | Description | Calculate call | Packet |
|---:|---:|---|---|---|
| 001 | 3976 | Bailey's Consumer 2019 | POST, 200 | `calls/00N-priceclass-3976/` |
| 002 | 346 | Baileys Moving & Storage | POST, 200 | `calls/00N-priceclass-346/` |
| 003 | 4235 | BGRS - Canada | POST, 200 | `calls/00N-priceclass-4235/` |
| 004 | 4257 | BGRS - Domestic - General Motors | POST, 200 | `calls/00N-priceclass-4257/` |

The per-variant HARs are retained under each `00N-priceclass-{id}/` folder. No `UpdateLeadEstimate` was observed in the isolated captures.


## P3-B level sequence

For each level: clear/filter Network → select Pricing Info Level → click Calculate Price → wait for totals → export sanitized HAR → write packet.

| Run | pricingLevelId | name | HTTP | Grand Total / SMF | HAR |
|---:|---:|---|---:|---:|---|
| B1 | 715 | Level 1 | 200 | 2593.08 / 310.42 | `p3b-level-715.har` |
| B2 | 718 | Level 4 | 200 | 2771.90 / 336.44 | `p3b-level-718.har` |
| B3 | 724 | Level 10 | 200 | 3189.15 / 397.15 | `p3b-level-724.har` |
| B4 | 804 | Level 20 (highest) | 200 | 4659.43 / 611.06 | `p3b-level-804.har` |

P3-A save probe: explicit Save fired `PUT Estimate/UpdateLeadEstimate?tabSwitchFlag=false` (HTTP 200), but the subsequent calculate DTO still reported `allianceDto.priceClassId: null`.
