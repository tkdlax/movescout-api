# 015-article-catalog (pointer)

Article catalog capture lives in the catalogs pack, not as a single Create/Update call.

- Canonical exports: `/workspace/movescout-exploration/flows/03-catalogs/article-catalog.json` (and `.csv`, `article-catalog-unique-by-id.json`)
- Per-room raw: `flows/03-catalogs/article-response-room-*.json`
- Endpoint: `GET Inventory/GetAllArticlesGroupByRoomSP`
- HAR: `flows/03-catalogs/network-articles-all-rooms.har` and `flows/03-article-catalog/network-article-catalog.har`

This folder is a pointer only — full header/body pairs are in the per-room response files and HAR.
