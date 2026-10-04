# MoveScout Pro API exploration

Working notes for expanding [tkdlax/movescout-api](https://github.com/tkdlax/movescout-api) by capturing live UI → `movescoutproapi.sirva.com` traffic.

## Hosts

| Role | URL |
|------|-----|
| Web UI | `https://movescoutpro.sirva.com` |
| Upstream API | `https://movescoutproapi.sirva.com` |
| Middleware (wrapper) | `https://mspapi.jbeckstead.com` |

## Already covered (do not re-document unless mapping changes)

See middleware README + `docs/movescout-api-catalog.md`: TokenAuth, GetAllLead, LOV, inventory/estimate *reads*, Alliance reference, appointments *list* (partial), sales reports, etc.

## Flow packets

Each flow under `flows/` pairs a UI narrative with ordered call detail folders.

| Flow | Status | Gap vs middleware |
|------|--------|-------------------|
| `01-create-lead-survey-estimate` | in progress | Create lead, create/set survey appointment, create estimate |
