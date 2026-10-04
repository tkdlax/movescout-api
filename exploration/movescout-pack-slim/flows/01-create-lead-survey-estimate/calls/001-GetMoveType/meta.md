# GetMoveType

- Method: `GET`
- URL: `https://movescoutproapi.sirva.com//api/services/app/Lead/GetMoveType?DesinationState=CA&OriginState=IL&DesinationCountry=US&OriginCountry=US`
- HTTP status: `200`
- UI timing/action: Post-form address-derived move type lookup in the save flow.
- HAR capture: DevTools Network Preserve log was enabled, log was cleared immediately before Save, and the Network filter was `movescoutproapi`.
- Request body file: `request.body.json` (`{}` means no request body; query parameters are in the URL).
- Sensitive header handling: Authorization/cookie/signature values are redacted in `request.headers.json`; header names are retained.
