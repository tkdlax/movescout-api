# MoveScout Pro API Catalog (Stub)

Field lists and payload shapes for MoveScout Pro API endpoints. Expand this document with HAR captures as needed.

## Authentication

`POST /api/TokenAuth/Authenticate`

```json
{
  "userNameOrEmailAddress": "user@example.com",
  "password": "password"
}
```

Response: `{ "result": { "accessToken": "..." } }`

## Leads

### GetAllLead

`POST /api/services/app/Lead/GetAllLead`

Key request fields: `defaultFilterLead`, `filters`, `page`, `pageSize`, `sortField`, `sortDir`

### GetLeadById

`GET /api/services/app/Lead/GetLeadById?leadId={id}`

### CreateOrUpdateLead

`POST /api/services/app/Lead/CreateOrUpdateLead`

Minimum create fields (TBD — confirm via HAR): firstName, lastName, phone, dispositionId, tenantId, mobileSyncFlag

## Activities

### GetAllActivitiesWithCombineData

`POST /api/services/app/Activity/GetAllActivitiesWithCombineData`

### CreateOrUpdateActivity

`POST /api/services/app/Activity/CreateOrUpdateActivity`

## Filterable Lead Fields

- agencyCode
- dispositionId
- salesRepName
- creationTime
- registrationNumber
- firstName, lastName, city, state, bookerName

See [movescout-middleware-project-plan.md](../movescout-middleware-project-plan.md) for filter syntax.
