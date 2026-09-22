# Notes

- UI action: selected **BGRS - Domestic - General Motors** in Price Class, then clicked Calculate Price.
- Observed response totals: `totalEstimationPriceNet=2771.9`, `totalSMFPriceNet=336.44`.
- Observed response `error`: `None`.
- The captured calculate payload and response both show `allianceDto.priceClassId: null`; therefore these totals are recorded as observed, but cannot be proven to be class-specific from this POST alone. No `UpdateLeadEstimate` call was present in this isolated HAR.
- No UI error was observed; Level 4, TPG, and load/deliver prerequisites were retained.
