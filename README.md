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
curl -H "X-API-Key: YOUR_KEY" "http://localhost:8000/leads?pageSize=1"
```

API docs (development only): http://localhost:8000/docs

## TrueNAS Scale Deployment

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
| GET | `/leads` | Paginated lead list |
| GET | `/leads/export` | CSV export |
| GET | `/leads/{id}` | Single lead |
| POST | `/leads` | Create lead |
| PUT | `/leads/{id}` | Update lead (fetch-merge-update) |
| POST | `/leads/query` | Generic filter query |
| GET | `/leads/{id}/appointments` | Lead appointments |
| POST | `/leads/{id}/appointments` | Create survey appointment |
| GET | `/appointments` | Cross-lead activity search |
| GET | `/appointments/latest-per-lead` | Deduplicated appointments |
| GET | `/queries/booked-no-reg` | Booked leads without reg number |
| GET | `/queries/scheduled-surveys` | Survey scheduled leads |
| GET | `/queries/unassigned` | Unassigned qualified leads |
| GET | `/queries/my-leads` | Leads for user's sales rep |

All endpoints except `/health` require `X-API-Key` header.

## Admin Scripts

```bash
# Create user
python scripts/create_user.py --name "User" --movescout-username "..." --movescout-password "..."

# Rotate API key
python scripts/rotate_api_key.py --user-id "<uuid>"
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
