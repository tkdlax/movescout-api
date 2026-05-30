# MoveScout Middleware API

REST API proxy for [MoveScout Pro](https://movescoutpro.sirva.com). Callers authenticate with an API key; the middleware handles MoveScout token management transparently.

## Features

- API key authentication (`X-API-Key` header)
- Encrypted MoveScout credential storage
- Per-user MoveScout token caching (24h expiry with 5-minute buffer)
- Lead CRUD, CSV export, appointments, and named queries
- Docker Compose deployment for TrueNAS Scale
- Cloud-ready (same image for AWS ECS / Azure Container Apps)

## Quick Start (Development)

```bash
# Copy and configure environment
cp .env.example .env

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Add the output to ENCRYPTION_KEY in .env

# Start stack
docker compose -f deploy/docker-compose.yml up -d --build

# Run migrations
docker compose -f deploy/docker-compose.yml run --rm api alembic upgrade head

# Create first user
docker compose -f deploy/docker-compose.yml run --rm api python scripts/create_user.py \
  --name "Admin" \
  --movescout-username "your@email.com" \
  --movescout-password "your-password" \
  --sales-rep-name "Your Name"

# Test
curl http://localhost:8000/health
curl -H "X-API-Key: YOUR_KEY" "http://localhost:8000/leads"
```

API docs (development only): http://localhost:8000/docs

## TrueNAS Scale Deployment

**Recommended:** [deploy/TRUENAS-CUSTOM-APP.md](deploy/TRUENAS-CUSTOM-APP.md) — Custom App via **Install via YAML** (clone repo to dataset + `include` compose file).

### Manual / CLI deployment

### 1. Prepare dataset

Create a dataset on TrueNAS Scale, e.g. `/mnt/tank/apps/movescout-api/`:

```bash
mkdir -p /mnt/tank/apps/movescout-api
cd /mnt/tank/apps/movescout-api
git clone <your-repo-url> .
cp .env.example .env
chmod 600 .env
```

Edit `.env` with production values:
- Set `ENVIRONMENT=production`
- Set `DISABLE_PUBLIC_DOCS=true`
- Generate and set `ENCRYPTION_KEY`
- Set strong `POSTGRES_PASSWORD`

### 2. Start production stack

```bash
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml up -d --build
docker compose -f deploy/docker-compose.yml run --rm api alembic upgrade head
docker compose -f deploy/docker-compose.yml run --rm api python scripts/create_user.py \
  --name "Admin" --movescout-username "..." --movescout-password "..."
```

The API binds to `127.0.0.1:8000` only — not exposed directly to the network.

### 3. Configure nginx reverse proxy

Copy [deploy/nginx/movescout-api.conf.example](deploy/nginx/movescout-api.conf.example) to your nginx host. Update:
- `server_name` to your domain
- `upstream` to point at TrueNAS IP (`http://<truenas-ip>:8000`)
- SSL certificate paths

Reload nginx after placing the config.

### 4. Firewall

- Allow inbound 443 to nginx only
- Block inbound 8000 from WAN
- Allow outbound HTTPS from TrueNAS to `movescoutpro.sirva.com`

### 5. Backups

Schedule TrueNAS dataset snapshots for the Postgres volume. Manual backup:

```bash
docker compose -f deploy/docker-compose.yml exec postgres \
  pg_dump -U movescout movescout > backup_$(date +%Y%m%d).sql
```

Restore:

```bash
cat backup.sql | docker compose -f deploy/docker-compose.yml exec -T postgres \
  psql -U movescout movescout
```

### 6. Upgrades

```bash
git pull
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml up -d --build
docker compose -f deploy/docker-compose.yml run --rm api alembic upgrade head
```

### 7. Autostart

Docker Compose services use `restart: unless-stopped`. Ensure the Docker service is enabled on TrueNAS Scale boot (default for custom apps).

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check (no auth) |
| GET | `/lov` | List-of-value enums from MoveScout (cached, `?refresh=true` to bypass) |
| GET | `/reference/service-items` | Alliance item master (482 items, cached) |
| GET | `/reference/service-item-types` | Alliance item types (cached) |
| GET | `/reference/service-item-categories` | Alliance categories (cached) |
| GET | `/reference/vehicles` | Auto make/model reference (cached) |
| GET | `/reference/transit-seasons` | Transit guide seasons (cached) |
| GET | `/reference/price-classes` | Alliance price classes (`?bookerId=`) |
| GET | `/leads/{id}/inventory` | **Primary estimate + room-grouped inventory (one call)** |
| GET | `/leads/{id}/pricing` | **Primary estimate + pricing JSON (one call)** |
| GET | `/leads/{id}/estimates` | List estimates for a lead |
| GET | `/leads/{id}/estimates/primary` | Primary estimate summary |
| GET | `/leads/{id}/estimates/{estimateId}` | Full estimate DTO (inventory tab) |
| GET | `/leads/{id}/estimates/{estimateId}/summary` | Room/segment inventory totals |
| GET | `/leads/{id}/estimates/{estimateId}/rooms` | Room reference list |
| GET | `/leads/{id}/estimates/{estimateId}/segments` | Estimate segments |
| GET | `/leads/{id}/estimates/{estimateId}/accessorials` | Accessorial charges |
| GET | `/leads/{id}/estimates/{estimateId}/pricing` | Pricing engine response |
| GET | `/leads/{id}/estimates/{estimateId}/tariffs` | Available tariffs |
| GET | `/leads/{id}/estimates/{estimateId}/auto-spot` | Auto spot details |
| GET | `/leads/{id}/estimates/{estimateId}/notes` | Customer-facing notes |
| GET | `/leads/{id}/estimates/{estimateId}/alliance` | Alliance quote record |
| GET | `/leads/{id}/estimates/{estimateId}/booker-id` | Booker/agency ID |
| GET | `/leads/page-count` | Total rows + page count for a query (probe only) |
| GET | `/leads` | One page of leads (`page`, `maxResultSize`) |
| GET | `/leads/export` | CSV export |
| GET | `/leads/{id}` | Single lead |
| POST | `/leads` | Create lead |
| PUT | `/leads/{id}` | Update lead (fetch-merge-update) |
| POST | `/leads/query/page-count` | Page count for a POST filter query |
| POST | `/leads/query` | One page of a filter query (`page`, `maxResultSize`) |
| GET | `/leads/{id}/appointments` | Lead appointments |
| POST | `/leads/{id}/appointments` | Create survey appointment |
| GET | `/appointments` | Cross-lead activity search |
| GET | `/appointments/latest-per-lead` | Deduplicated appointments |
| GET | `/queries/booked-no-reg` | Booked leads without reg number |
| GET | `/queries/scheduled-surveys` | Survey scheduled leads |
| GET | `/queries/unassigned` | Unassigned qualified leads |
| GET | `/queries/my-leads` | Leads for user's sales rep |
| POST | `/reports/sales` | Enqueue async sales report job (returns `reportId`) |
| GET | `/reports/sales/{reportId}` | Poll/download completed report (`409` while running) |

All endpoints except `/health` require `X-API-Key` header.

### Sales report

Reports run as background jobs so generation is not limited by HTTP/proxy timeouts.

1. **`POST /reports/sales`** — enqueue job with JSON body, returns **202** with `{ reportId, status, expiresAt }`
2. **`GET /reports/sales/{reportId}`** — poll until **200** HTML download (`409` while pending/running)

JSON body (POST):

| Field | Default | Notes |
|-------|---------|-------|
| `moveType` | `Interstate` | |
| `start` | Jan 1 of current year | |
| `end` | Today | |
| `location` | Bailey's Moving & Storage | |
| `goal` | `0.40` | |
| `salesRepName` | (none) | Optional filter |
| `defaultFilter` | `3` | |
| `callbackUrl` | (none) | Per-client webhook; middleware POSTs JSON when job completes |

When the job finishes (`ready` or `failed`), the middleware POSTs to `callbackUrl`:

```json
{
  "reportId": "...",
  "status": "ready",
  "downloadUrl": "https://mspapi.jbeckstead.com/reports/sales/...",
  "expiresAt": "...",
  "filename": "sales-interstate-20260530.html",
  "error": null
}
```

Set `API_PUBLIC_BASE_URL=https://mspapi.jbeckstead.com` in `.env` so `downloadUrl` is absolute.

**Zapier / URL-based fetch:** append your API key as a query param (same auth as the header):

```text
{{downloadUrl}}?X-API-Key=YOUR_KEY
```

Use that full URL as the email attachment source or any HTTP GET step. The download endpoint also accepts `X-API-Key` as a header.

Optional env `REPORT_CALLBACK_SECRET` adds `Authorization: Bearer ...` on outbound webhooks.

Files expire after **1 hour** (`REPORT_TTL_SECONDS`, default 3600). Metadata in Postgres; HTML on disk (`REPORT_STORAGE_DIR`).

After deploy, run `alembic upgrade head` once to create the `report_jobs` table.

```powershell
$body = @{
  moveType = "Interstate"
  start = "Jan 1, 2026"
  end = "May 29, 2026"
  callbackUrl = "https://your-client-flow.webhook.office.com/..."
} | ConvertTo-Json

$job = Invoke-RestMethod -Method POST `
  -Uri "https://mspapi.jbeckstead.com/reports/sales" `
  -Headers @{ "X-API-Key" = $apiKey; "Content-Type" = "application/json" } `
  -Body $body

# Optional: poll if not using callbackUrl
Invoke-WebRequest `
  -Uri "https://mspapi.jbeckstead.com/reports/sales/$($job.reportId)" `
  -Headers @{ "X-API-Key" = $apiKey } `
  -OutFile "report.html"
```

Optional env `REPORT_MAX_LEADS` fails the job if the probe count exceeds the cap.

## Admin Scripts

```bash
# Create user
python scripts/create_user.py --name "User" --movescout-username "..." --movescout-password "..."

# Rotate API key
python scripts/rotate_api_key.py --user-id "<uuid>"

# Smoke-test inventory for a lead
python scripts/test_inventory_by_lead.py --lead-id 1553516 --api-key YOUR_KEY
```

## Cloud Migration

See [deploy/terraform/README.md](deploy/terraform/README.md) for AWS/Azure migration runbook. The same Docker image and environment variables work across all hosts.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check app tests scripts
uvicorn app.main:app --reload
```

## Project Structure

See [movescout-middleware-project-plan.md](movescout-middleware-project-plan.md) for the full API specification and filter mapping reference.
