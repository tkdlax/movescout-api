# Cloud Migration Runbook

This document describes how to migrate the MoveScout Middleware API from TrueNAS Scale (Docker Compose) to AWS or Azure using the same container image.

## Prerequisites

- Container image published to a registry (GHCR, ECR, or ACR)
- Managed PostgreSQL instance provisioned
- Secrets stored in cloud secret manager
- DNS control for your API domain

## Environment Variables (unchanged across hosts)

| Variable | TrueNAS | AWS | Azure |
|---|---|---|---|
| `DATABASE_URL` | Compose postgres service | RDS connection string | Azure PG connection string |
| `ENCRYPTION_KEY` | `.env` file | Secrets Manager | Key Vault |
| `MOVESCOUT_BASE_URL` | env | env | env |
| `ENVIRONMENT` | `production` | `production` | `production` |
| `DISABLE_PUBLIC_DOCS` | `true` | `true` | `true` |

## Migration Steps

### 1. Backup Postgres on TrueNAS

```bash
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml exec postgres \
  pg_dump -U movescout movescout > movescout_backup.sql
```

### 2. Publish Container Image

```bash
docker build -t ghcr.io/your-org/movescout-api:v0.1.0 .
docker push ghcr.io/your-org/movescout-api:v0.1.0
```

### 3. Provision Cloud Infrastructure

**AWS (recommended path):**
- ECS Fargate cluster + task definition (same image)
- RDS PostgreSQL 16
- ALB with ACM certificate
- Secrets Manager for `ENCRYPTION_KEY` and `DATABASE_URL`
- Expand `deploy/terraform/aws/main.tf`

**Azure:**
- Azure Container Apps
- Azure Database for PostgreSQL Flexible Server
- Key Vault for secrets
- Application Gateway or Front Door for TLS
- Expand `deploy/terraform/azure/main.tf`

### 4. Restore Database

```bash
psql "$DATABASE_URL" < movescout_backup.sql
```

Or use managed restore from snapshot if using RDS/Azure backup tools.

### 5. Deploy Container

Point the cloud container service at the published image with the same env vars. Run migrations if needed:

```bash
alembic upgrade head
```

### 6. Smoke Tests

```bash
curl https://api.yourdomain.com/health
curl -H "X-API-Key: YOUR_KEY" https://api.yourdomain.com/leads?pageSize=1
```

### 7. DNS Cutover

Update DNS to point `api.yourdomain.com` to the cloud load balancer. Keep TrueNAS stack running briefly for rollback.

### 8. Decommission TrueNAS Stack

After validation period:

```bash
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml down
```

## Rollback

Revert DNS to TrueNAS nginx upstream. TrueNAS stack should remain intact until migration is validated.

## No Application Code Changes Required

The same Docker image and environment contract work on TrueNAS, AWS ECS Fargate, and Azure Container Apps.
