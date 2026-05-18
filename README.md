# dcmapper

Static, security-first Python web app to catalog and publish a map of known local datacenter-related facilities (business datacenters, local government facilities, colocation sites, telco central offices, etc.).

## Documentation

- For complete installation, usage, CLI, API, operations, and troubleshooting guidance, see `USER_GUIDE.md`.

## Project Goal

Build a small, containerized Python application that:
- serves a rendered map from a curated database of GPS points and metadata,
- remains mostly static/read-only for web users,
- does **not** allow location creation or editing from the website,
- uses an admin-only Python CLI tool to add/update records in the database.

This project is intentionally scoped for local/regional known facilities, not global-scale datacenter market tracking.

## High-Level Architecture

- **Web app**: Python `FastAPI` service with server-side rendered pages (`Jinja2`).
- **Map rendering**: Leaflet.js in the browser with markers loaded from read-only API endpoints.
- **Database**: PostgreSQL (preferred) or SQLite for local dev; PostgreSQL in production.
- **Admin ingestion**: Separate Python CLI script (`Typer`) for prompting and writing records.
- **Containerization**: Dockerfile + docker-compose for reproducible local and production-like deployments.

## Core Functional Requirements

- Public map page with markers for all published facilities.
- Marker popup/details include metadata (name, entity type, city, notes, confidence, sources).
- Optional filter controls (type, city, operator) implemented as URL query params.
- Read-only web API endpoints for map data (`GET` only).
- Admin CLI for:
  - prompting for required data fields,
  - validating coordinates and enums,
  - inserting/updating records in DB,
  - soft-disabling incorrect records.

## Non-Functional Requirements

- Security-first defaults, minimal attack surface.
- Deterministic and easy container build.
- Small operational footprint, simple backup/restore.
- Clear audit trail for who/when entries were changed (via CLI metadata fields).

## Data Model (Initial)

Single primary table is enough for v1:

- `id` (UUID, PK)
- `name` (text, required)
- `entity_type` (enum: `enterprise`, `government`, `colo`, `telco_co`, `other`)
- `latitude` (numeric, required)
- `longitude` (numeric, required)
- `address` (text, optional)
- `city` (text, optional)
- `region` (text, optional)
- `country` (text, default `US` or configurable)
- `operator` (text, optional)
- `status` (enum: `known`, `suspected`, `retired`)
- `confidence` (integer 1-5)
- `source` (text, required; citation or origin note)
- `notes` (text, optional)
- `is_public` (boolean default true)
- `created_at`, `updated_at` (timestamps)
- `created_by`, `updated_by` (admin identifier from CLI)

Recommended indexes:
- geospatial index for coordinates (PostGIS later if needed),
- btree indexes on `entity_type`, `city`, `is_public`.

## Security Model

- No public write endpoints in the web app.
- Map/API routes expose only `is_public = true` records.
- Admin CLI is run out-of-band (inside trusted network or admin workstation).
- DB credentials passed via environment variables/secrets, never hardcoded.
- Container runs as non-root user.
- Restrictive CORS, security headers, and basic rate limiting on public endpoints.
- Optional basic auth for non-public deployments.

## Suggested Repository Structure

```text
dcmapper/
  app/
    main.py
    api/
      public.py
    templates/
      index.html
    static/
      css/
      js/
    db/
      models.py
      session.py
  alembic/
    env.py
    versions/
  tools/
    admin_cli.py
  tests/
    test_public_api.py
    test_cli_validation.py
  Dockerfile
  docker-compose.yml
  requirements.txt (or pyproject.toml)
  README.md
```

## Quick Start

- Copy `.env.example` to `.env` and adjust values as needed.
- Install dependencies: `pip install -r requirements.txt`
- Run migrations: `alembic upgrade head`
- Start app: `uvicorn app.main:app --reload`
- Add records via CLI: `python tools/admin_cli.py add-location`
- Bulk seed via file: `python tools/admin_cli.py seed ./locations.json`

## Development Plan

### Phase 1 - Foundation (Day 1-2)
- Initialize Python project (`FastAPI`, `SQLAlchemy`, `Alembic`, `Jinja2`, `Typer`).
- Create DB schema and first migration.
- Add seed data support (JSON/CSV import utility).
- Build base Dockerfile and docker-compose (app + db).

### Phase 2 - Read-Only Map UI (Day 2-4)
- Implement `GET /` map page and `GET /api/locations` endpoint.
- Render markers from DB and show metadata popups.
- Add simple filtering by type/city/operator.
- Ensure all endpoints are read-only and return only public fields.

### Phase 3 - Admin CLI Tool (Day 4-5)
- Build interactive CLI prompt flow for record creation.
- Add coordinate validation (`-90..90`, `-180..180`) and enum validation.
- Add update/deactivate commands by `id` or `name`.
- Record `created_by/updated_by` metadata with each change.

### Phase 4 - Security Hardening (Day 5-6)
- Remove/disable unused HTTP methods globally where possible.
- Add secure headers, strict CORS policy, and request size limits.
- Add database role separation (read-only web user, write-capable admin user).
- Validate container as non-root and pin dependency versions.

### Phase 5 - Testing and Packaging (Day 6-7)
- Unit tests for model and validation logic.
- API tests for public read-only behavior.
- CLI tests for prompt validation paths.
- Finalize compose profile and startup docs for local/prod.

## Minimal API Surface (v1)

- `GET /` -> map UI
- `GET /api/locations` -> JSON list of public points
- `GET /healthz` -> health check

No POST/PUT/DELETE endpoints exposed publicly in v1.

## Admin CLI Workflow (v1)

1. Admin runs `python tools/admin_cli.py add-location`.
2. CLI prompts for all required fields and validates each input.
3. CLI displays summary and asks for confirmation.
4. On confirm, record is inserted/updated in DB.
5. Change is visible on map after next app refresh.

## Deployment Notes

- Use `docker compose up -d` for app + db.
- Persist DB via named volume.
- Back up DB daily (logical dump).
- Keep `.env` out of git; provide `.env.example`.

### Container images (CI)

GitHub Actions (`.github/workflows/docker.yml`) builds the app image from `Dockerfile` on pushes to `main`, pull requests against `main`, version tags (`v*`), and manual workflow dispatch. Successful builds on `main` and tagged releases are published to GitHub Container Registry as `ghcr.io/<owner>/dcmapper` (`latest`, semver tags, and `sha-<commit>`). Pull requests build the image but do not push.

## Future Enhancements (Optional)

- PostGIS support for radius/nearby search.
- Source-link attachments and evidence tracking.
- Record review workflow (`draft` -> `published`).
- Map clustering for larger datasets.
