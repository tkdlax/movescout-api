# TrueNAS Scale Deployment Guide

This guide covers deploying the MoveScout Middleware API on TrueNAS Scale using Docker Compose behind an existing nginx reverse proxy.

## Requirements

- TrueNAS Scale with Docker enabled
- nginx host for TLS termination (can be on TrueNAS or a separate machine)
- Outbound HTTPS to `movescoutpro.sirva.com`
- Dataset for persistent Postgres storage

## Directory Layout on TrueNAS

```
/mnt/tank/apps/movescout-api/
├── .env                          # secrets (chmod 600)
├── deploy/
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
└── postgres-data/                # optional bind mount override
```

## Initial Setup

```bash
cd /mnt/tank/apps/movescout-api
git clone <repo-url> .
cp .env.example .env
chmod 600 .env
```

Edit `.env`:

```env
ENVIRONMENT=production
DISABLE_PUBLIC_DOCS=true
POSTGRES_PASSWORD=<strong-password>
ENCRYPTION_KEY=<fernet-key>
```

Generate Fernet key:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Start Services

```bash
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml up -d --build
docker compose -f deploy/docker-compose.yml run --rm api alembic upgrade head
docker compose -f deploy/docker-compose.yml run --rm api python scripts/create_user.py \
  --name "Admin" \
  --movescout-username "user@example.com" \
  --movescout-password "secret"
```

## nginx Configuration

1. Copy `deploy/nginx/movescout-api.conf.example` to your nginx host
2. Set upstream to TrueNAS IP: `server <truenas-ip>:8000;`
3. Configure Let's Encrypt certificates
4. Reload nginx: `nginx -s reload`

The API binds to `127.0.0.1:8000` on the Docker host. If nginx runs on a different machine, change the compose port mapping to expose 8000 on the TrueNAS LAN IP (firewall-restricted):

```yaml
ports:
  - "<truenas-lan-ip>:8000:8000"
```

## Firewall Checklist

| Rule | Action |
|---|---|
| WAN → nginx:443 | Allow |
| WAN → TrueNAS:8000 | Deny |
| TrueNAS → sirva.com:443 | Allow |

## Backups

### Dataset Snapshots

Schedule TrueNAS snapshots on the app dataset (recommended: daily, retain 7–30 days).

### Manual Postgres Dump

```bash
docker compose -f deploy/docker-compose.yml exec postgres \
  pg_dump -U movescout movescout | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore

```bash
gunzip -c backup_20260529.sql.gz | \
  docker compose -f deploy/docker-compose.yml exec -T postgres \
  psql -U movescout movescout
```

## Upgrades

```bash
git pull
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml up -d --build
docker compose -f deploy/docker-compose.yml run --rm api alembic upgrade head
```

Or pull a tagged image from a registry:

```bash
docker pull ghcr.io/your-org/movescout-api:v0.1.0
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml up -d
```

## Autostart on Reboot

Both services use `restart: unless-stopped`. Verify Docker starts on boot:

```bash
systemctl is-enabled docker
```

After a reboot, confirm services are running:

```bash
docker compose -f deploy/docker-compose.yml ps
curl http://127.0.0.1:8000/health
```

## Troubleshooting

| Symptom | Check |
|---|---|
| 502 from nginx | `docker compose logs api` — is the container running? |
| Report job failed | Check `docker compose logs api`; narrow date range or set `REPORT_MAX_LEADS` |
| Auth failures | Verify MoveScout credentials via `create_user.py` |
| DB connection errors | `docker compose logs postgres` — is Postgres healthy? |
| Token expiry mid-export | Normal — middleware auto-refreshes; check MoveScout connectivity |

## Smoke Test

```bash
curl https://api.yourdomain.com/health
curl -H "X-API-Key: YOUR_KEY" "https://api.yourdomain.com/leads?pageSize=1"
```
