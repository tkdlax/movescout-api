# UI narrative — P1 Stock (library) articles + pricing recalc

Status: **in progress**

## Goal

On estimate `2395896` (lead `1674404`, TPG), add **library/catalog** articles by existing `articleId` (not `CreateArticleFromInventory` customs). Capture payloads, then recalculate pricing.

## Planned

1. Open estimate inventory
2. Add 2–4 stock articles from catalog (e.g. Living Room / Bedroom library items) with qty ≥1
3. Save inventory
4. Calculate Price (keep existing price class/level/dates if still set; re-set if cleared)
5. Document call folders + contrast vs custom-article path

## Actual steps

_Starting…_
