# Notes

- After explicit Save, Calculate Price was run on estimate `2395896` with TPG and Level 4.
- Request and response both retained `allianceDto.priceClassId: null`; no non-null class ID was observed.
- HTTP 200; observed `totalEstimatinPriceNet=2771.9`, nested `totalSMFPriceNet=336.44`.

- Shared HAR: `00N-persistence-priceclass-3976/persistence-priceclass-3976-save-calc.har` covers both persistence packets; update-packet copy: `calls/p3a-persistence-3976-update/persistence-priceclass-3976-save-calc.har`.
