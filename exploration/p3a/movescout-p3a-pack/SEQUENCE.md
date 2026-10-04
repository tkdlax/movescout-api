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
