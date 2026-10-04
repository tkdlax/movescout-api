# 07-CreateOrUpdateArticleForListInventory-stock-aircon-870

- HAR entry index: 242
- Method: `POST`
- URL: `https://movescoutproapi.sirva.com//api/services/app/Inventory/CreateOrUpdateArticleForListInventory`
- HTTP status: 200
- Estimate: `2395896`
- Lead: `1674404`
- UI action: Inventory → Living Room → select catalog **Air Conditioner** (article `870`, code `V005`) once, changing shipping quantity from 1 to 2, then Save.
- Payload contains the full inventory-row array as observed in live traffic; `isCustomArticle:false` for catalog Air Conditioner.
