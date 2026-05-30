# TrueNAS Scale — Custom App deployment

This guide uses **Apps → Install via YAML**, which is the right way to run a multi-container stack (Postgres + API) on TrueNAS Scale 24.10+.

TrueNAS does **not** run `git clone` inside the Custom App wizard. You clone the repo to a **dataset** once, point the app at that path, then manage updates with `git pull`.

---

## Overview

| Step | What |
|------|------|
| 1 | Create a dataset for the app |
| 2 | Clone `https://github.com/tkdlax/movescout-api` onto that dataset |
| 3 | Create `.env` with secrets |
| 4 | Install Custom App via YAML (`include` → `truenas-compose.yml`) |
| 5 | Run migrations + create API user (shell on TrueNAS) |
| 6 | Point nginx at TrueNAS port 8000 |

---

## Requirements

- TrueNAS **Scale 24.10 (Electric Eel)** or newer (Docker-based Apps)
- Outbound HTTPS to `movescoutpro.sirva.com`
- MoveScout Pro username/password
- App name in UI: **`movescout-api`** (lowercase, letters/numbers/hyphens only)

---

## Step 1 — Create a dataset

1. **Storage → Datasets → Add Dataset**
2. Example name: `tank/apps/movescout-api`
3. Full path will look like: `/mnt/tank/apps/movescout-api`

You will store:

- Git clone (application code)
- `.env` (secrets)
- `postgres-data/` (database files)

---

## Step 2 — Clone the GitHub repo onto TrueNAS

Open **Shell** on TrueNAS (or SSH):

```bash
cd /mnt/tank/apps/movescout-api
git clone https://github.com/tkdlax/movescout-api.git .
```

If the repo is **private**, use a personal access token or SSH:

```bash
git clone git@github.com:tkdlax/movescout-api.git .
```

Verify files exist:

```bash
ls -la
# Should see: app/  deploy/  Dockerfile  pyproject.toml  .env.example
```

---

## Step 3 — Create `.env`

```bash
cd /mnt/tank/apps/movescout-api
cp .env.example .env
chmod 600 .env
nano .env   # or edit via TrueNAS UI / SMB
```

Set at minimum:

```env
ENVIRONMENT=production
DISABLE_PUBLIC_DOCS=true

POSTGRES_USER=movescout
POSTGRES_PASSWORD=<strong-random-password>
POSTGRES_DB=movescout

ENCRYPTION_KEY=<fernet-key>

MOVESCOUT_BASE_URL=https://movescoutpro.sirva.com
LOG_LEVEL=info
RATE_LIMIT_PER_MINUTE=60

# Must match where you cloned the repo (for Postgres host volume)
APP_DATA_PATH=/mnt/tank/apps/movescout-api
```

Generate `ENCRYPTION_KEY`:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Create Postgres data directory:

```bash
mkdir -p /mnt/tank/apps/movescout-api/postgres-data
```

---

## Step 4 — Install the Custom App (YAML)

### 4a. Open the installer

1. **Apps → Discover Apps**
2. Click the **⋮** (three dots) near **Custom App**
3. Choose **Install via YAML** (not the single-container “Custom App” wizard)

### 4b. App name

- **Name:** `movescout-api`  
  (must start with a letter, lowercase, hyphens OK, no leading/trailing hyphen)

### 4c. Custom Config

Edit [truenas-custom-app.yaml](truenas-custom-app.yaml) so the `include` path matches your dataset:

```yaml
include:
  - /mnt/tank/apps/movescout-api/deploy/truenas-compose.yml
```

Paste that into the **Custom Config** box.

> **TrueNAS 25.10+:** If the UI rejects YAML with only `include:`, try adding an empty services block (check your version’s docs):
>
> ```yaml
> services: {}
> include:
>   - /mnt/tank/apps/movescout-api/deploy/truenas-compose.yml
> ```

### 4d. Save and wait

Click **Save**. TrueNAS pulls images and starts containers. First deploy may take several minutes.

- **Postgres:** `postgres:16-alpine`
- **API:** `ghcr.io/tkdlax/movescout-api:latest` (built by GitHub Actions)

If the API image pull fails (package not public yet), see **“Build image on TrueNAS”** below.

### 4e. Check status

**Apps → Installed Applications → movescout-api**

Both services should be running. On TrueNAS shell:

```bash
curl http://127.0.0.1:8000/health
```

Expected: `{"status":"ok"}`

---

## Step 5 — Database migration and first user

Run these **once** from TrueNAS shell (adjust app name if different):

```bash
cd /mnt/tank/apps/movescout-api

# Find the running API container name (often includes movescout-api)
docker ps --format "{{.Names}}" | grep -i api

# Run migration (replace CONTAINER with actual api container name)
docker exec -it <api-container-name> alembic upgrade head

# Create first user — save the printed API key
docker exec -it <api-container-name> python scripts/create_user.py \
  --name "Your Name" \
  --movescout-username "your@email.com" \
  --movescout-password "your-movescout-password" \
  --sales-rep-name "Your Name"
```

Alternative if `docker compose` is available on the host:

```bash
cd /mnt/tank/apps/movescout-api
docker compose -f deploy/truenas-compose.yml run --rm api alembic upgrade head
docker compose -f deploy/truenas-compose.yml run --rm api python scripts/create_user.py \
  --name "Your Name" \
  --movescout-username "your@email.com" \
  --movescout-password "your-password" \
  --sales-rep-name "Your Name"
```

Test:

```bash
curl -H "X-API-Key: YOUR_KEY" "http://127.0.0.1:8000/leads?pageSize=1"
```

---

## Step 6 — nginx (HTTPS)

The stack exposes port **8000** on the TrueNAS host.

- **nginx on the same TrueNAS:** upstream `127.0.0.1:8000`
- **nginx on another machine:** upstream `<truenas-lan-ip>:8000` and firewall allow only nginx → 8000

Use [nginx/movescout-api.conf.example](nginx/movescout-api.conf.example). Change upstream if needed:

```nginx
upstream movescout_api {
    server <TRUENAS_IP>:8000;
}
```

---

## Updating the app

```bash
cd /mnt/tank/apps/movescout-api
git pull
```

Then in TrueNAS UI:

**Apps → movescout-api → Update / Redeploy** (wording varies by version)

Or restart from shell after pull:

```bash
# Redeploy pulls latest ghcr.io image if using image: in truenas-compose.yml
```

Run migrations after updates if the repo added new Alembic revisions:

```bash
docker exec -it <api-container-name> alembic upgrade head
```

---

## Build image on TrueNAS (if GHCR pull fails)

Edit `deploy/truenas-compose.yml` on the dataset:

1. Comment out `image:` and `pull_policy:`
2. Uncomment the `build:` block

Redeploy the Custom App from the UI. TrueNAS will build from the cloned repo (slower, but works offline from GHCR).

---

## Make GHCR image public (one-time)

After the first GitHub Actions run:

1. GitHub → **tkdlax/movescout-api** → **Packages** (or org packages)
2. Open **movescout-api** package → **Package settings** → change visibility to **Public**  
   (or configure TrueNAS to authenticate to GHCR for private packages)

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| YAML validation error | Check `include` path exists; app name is valid |
| API container won’t start | Apps → movescout-api → Logs; verify `.env` and `ENCRYPTION_KEY` |
| `POSTGRES_PASSWORD` error | `.env` must set `POSTGRES_PASSWORD` (compose requires it) |
| Image pull 401/404 | Build locally (above) or publish/make GHCR package public |
| Health OK but 502 on `/leads` | MoveScout credentials; outbound firewall to sirva.com |
| Postgres permission errors | `chown`/`chmod` on `postgres-data` or recreate empty dir |

---

## Why not the single-container “Custom App” wizard?

That wizard installs **one** Docker image. This project needs **Postgres + API**. **Install via YAML** with Compose is the supported approach for multi-service stacks on TrueNAS Scale.

---

## Quick reference paths

| Item | Path |
|------|------|
| Repo clone | `/mnt/tank/apps/movescout-api` |
| Secrets | `/mnt/tank/apps/movescout-api/.env` |
| Compose file | `/mnt/tank/apps/movescout-api/deploy/truenas-compose.yml` |
| UI YAML snippet | `/mnt/tank/apps/movescout-api/deploy/truenas-custom-app.yaml` |
| Postgres data | `/mnt/tank/apps/movescout-api/postgres-data` |
