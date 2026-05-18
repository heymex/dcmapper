# dcmapper User Guide

This guide explains how to install, configure, run, and operate `dcmapper` as an end user or administrator.

## Who This Is For

- **Map viewer (read-only user):** opens the web map and consumes public JSON data.
- **Operator (service owner):** deploys and runs the web app and database.
- **Admin curator:** adds and manages facility records via the admin CLI.

## What dcmapper Does

`dcmapper` publishes a read-only map of datacenter-related facilities. Public users can only read data. Record creation and bulk ingestion happen through a separate admin CLI.

## Key Concepts

- **Public record:** a location where `is_public=true`; visible in the website/API.
- **Private record:** a location where `is_public=false`; stored in DB but hidden from public API.
- **Source/citation:** required provenance for each record.
- **Confidence:** integer score from `1` to `5`.

## Prerequisites

- Python 3.12+ recommended
- `pip`
- Docker + Docker Compose (if running with containers)
- PostgreSQL (for production-like deployments) or SQLite (for local dev)

## Quick Start (Local Python)

1. From the repository root, create and activate a virtual environment.
2. Install dependencies.
3. Configure environment values.
4. Run migrations.
5. Start the app.

Example:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Open: [http://localhost:8000](http://localhost:8000)

## Quick Start (Docker Compose)

From the repository root:

```bash
docker compose up -d --build
```

Then open: [http://localhost:8000](http://localhost:8000)

Notes:
- Compose starts `web` and `db`.
- PostgreSQL data is persisted in the `pgdata` volume.

## Configuration

Copy `.env.example` to `.env` and adjust:

- `DATABASE_URL`  
  - SQLite example: `sqlite:///./dcmapper.db`
  - Postgres example: `postgresql+psycopg2://dcmapper:dcmapper@db:5432/dcmapper`
- `DCMAPPER_ADMIN_NAME`  
  - Default admin identifier used by CLI if prompt is skipped.
- `ALLOWED_ORIGINS`  
  - Comma-separated list for CORS (for browser clients).
- `RATE_LIMIT_WINDOW_SECONDS`  
  - API rate limit window size.
- `RATE_LIMIT_MAX_REQUESTS`  
  - Max API requests per client per window.
- `DCMAPPER_AUTO_CREATE_SCHEMA`  
  - `true` only for local experimentation; prefer Alembic migrations.

## Running Migrations

Use Alembic for schema management:

```bash
alembic upgrade head
```

When adding new schema changes in development:

```bash
alembic revision -m "describe change"
alembic upgrade head
```

## Using the Web UI (Read-Only)

1. Open `/`.
2. Map loads markers from `GET /api/locations`.
3. Click marker popups for facility metadata:
   - Name
   - Entity type
   - City
   - Operator
   - Confidence

If no records are visible, confirm:
- there are records in DB,
- records are `is_public=true`,
- API is healthy at `/healthz`.

## Public API Reference

### `GET /`

- Returns rendered HTML map page.

### `GET /api/locations`

- Returns JSON list of public locations.
- Includes only public-safe fields (no internal audit fields).

Example response item:

```json
{
  "id": "f2f9ccf3-2f38-4898-8d90-1a4b3d8fdaf5",
  "name": "Example Facility",
  "entity_type": "colo",
  "latitude": 34.0522,
  "longitude": -118.2437,
  "city": "Los Angeles",
  "region": "CA",
  "country": "US",
  "operator": "Example Operator",
  "status": "known",
  "confidence": 4,
  "source": "https://example.org/source",
  "notes": "Public notes"
}
```

### `GET /healthz`

- Returns `{ "status": "ok" }` when app is alive and DB is reachable.

## Admin CLI Reference

Admin writes are performed through `tools/admin_cli.py`.

### `add-location`

Interactive add flow:

```bash
python tools/admin_cli.py add-location
```

Prompts include:
- facility name
- entity type (`enterprise|government|colo|telco_co|other`)
- latitude/longitude (validated ranges)
- source/citation (required, non-empty; URL host validated when using `http(s)`)
- optional metadata (`city`, `region`, `operator`, `notes`)
- confidence (`1-5`)
- status (`known|suspected|retired`)
- public visibility toggle

### `seed`

Bulk import from JSON or CSV:

```bash
python tools/admin_cli.py seed ./locations.json
python tools/admin_cli.py seed ./locations.csv
```

CSV/JSON should provide fields expected by the CLI importer (required at minimum: `name`, `entity_type`, `latitude`, `longitude`, `source`).

### `list-locations`

List all records (public and private):

```bash
python tools/admin_cli.py list-locations
```

## Seed File Examples

### JSON

```json
[
  {
    "name": "Metro Colo A",
    "entity_type": "colo",
    "latitude": 33.749,
    "longitude": -84.388,
    "city": "Atlanta",
    "region": "GA",
    "country": "US",
    "operator": "Example Operator",
    "status": "known",
    "confidence": 4,
    "source": "https://example.org/reference",
    "notes": "Local hub",
    "is_public": true
  }
]
```

### CSV

```csv
name,entity_type,latitude,longitude,city,region,country,operator,status,confidence,source,notes,is_public
Metro Colo A,colo,33.749,-84.388,Atlanta,GA,US,Example Operator,known,4,https://example.org/reference,Local hub,true
```

## Security and Access Model

- Web app exposes read-only routes.
- API only serves records with `is_public=true`.
- Admin CLI is the write path; run it on trusted hosts.
- Security headers and API rate limiting are enabled by default.
- Container image runs as non-root user.

## Backups and Restore

For PostgreSQL deployments, run logical backups regularly.

Backup:

```bash
pg_dump -Fc "$DATABASE_URL" > "backup_$(date +%Y%m%d_%H%M%S).dump"
```

Restore:

```bash
pg_restore -d "$DATABASE_URL" --clean "/path/to/backup.dump"
```

Recommendations:
- keep backups off-host,
- test restore periodically,
- document retention policy.

## Operations Checklist

- App healthy at `/healthz`
- DB migrations up to date
- `.env` values correct for environment
- Backups running and restorable
- `ALLOWED_ORIGINS` restricted to required origins
- Admin access limited to trusted users

## Troubleshooting

### API returns 429 (rate limit exceeded)

- Increase `RATE_LIMIT_MAX_REQUESTS` or `RATE_LIMIT_WINDOW_SECONDS` as needed.
- Check if client/proxy causes many requests from one source IP.

### Map loads but shows no markers

- Verify `/api/locations` returns data.
- Ensure records are marked `is_public=true`.
- Confirm coordinates are valid.

### `/healthz` fails

- Check DB availability and `DATABASE_URL`.
- Confirm DB credentials and network reachability.

### CLI import fails on row validation

- Check enum values:
  - `entity_type`: `enterprise|government|colo|telco_co|other`
  - `status`: `known|suspected|retired`
- Verify `confidence` is `1-5`.
- Ensure `source` is non-empty.

## Testing

Run tests:

```bash
pytest -q
```

## Versioning and Upgrades

- Upgrade dependencies deliberately.
- Run migrations before deploying new app versions.
- Validate `/healthz` and `/api/locations` after deployment.

## Support Notes

This project is intentionally scoped to curated, local/regional facility datasets. For larger scale geospatial querying, consider future PostGIS enhancements.
