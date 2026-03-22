# DB API

Metadata-driven backend built with FastAPI and PostgreSQL.

## Current Scope

The application now exposes a generic runtime-configurable data model instead of fixed domain tables.

Core tables:

- `users`
- `schemas`
- `fields`
- `entries`
- `entry_relations`
- `entry_history`
- `attachments`
- `entry_permissions`

`entry_history` is the only change-tracking mechanism. Request-level audit logs were removed.

## API Overview

Base URL (local): `http://localhost:8000`

Main routes:

- `POST /auth/login`
- `GET /auth/me`
- `PATCH /auth/me`
- `GET /users`
- `POST /users`
- `PATCH /users/{user_id}`
- `PATCH /users/{user_id}/status`
- `DELETE /users/{user_id}`
- `GET /schemas`
- `POST /schemas`
- `GET /schemas/{schema_id}`
- `POST /schemas/{schema_id}/fields`
- `GET /entries`
- `POST /entries`
- `GET /entries/{entry_id}`
- `PATCH /entries/{entry_id}`
- `GET /entries/{entry_id}/history`
- `GET /entries/{entry_id}/relations`
- `POST /entries/{entry_id}/relations`
- `GET /entries/{entry_id}/permissions`
- `POST /entries/{entry_id}/permissions`
- `GET /entries/{entry_id}/attachments`
- `POST /entries/{entry_id}/attachments`

## Global Roles

The system currently uses these global roles:

- `head_admin`: full access, including creating and assigning `admin` and `head_admin`
- `admin`: full access except creating or assigning `admin` and `head_admin`
- `manager`: can manage schemas and entries, but not users
- `editor`: can work with entries, but not users or schema definitions
- `reader`: read-only role

## Attachment Model

Attachments are external links only. The backend stores metadata plus a URL like a Google Drive link.
This fits Railway deployment because no local filesystem persistence is required.

Example:

```json
{
  "file_name": "contract.pdf",
  "external_url": "https://drive.google.com/file/d/abc/view",
  "mime_type": "application/pdf",
  "file_size": 123456,
  "description": "External reference"
}
```

## Structure

- `api/app/routers`: HTTP endpoints
- `api/app/schemas.py`: request and response DTOs
- `api/app/repositories`: SQL access layer
- `api/app/services`: business logic
- `api/app/validation`: dynamic field validation
- `api/app/permissions`: access control
- `db/init.sql`: database schema
- `docs/metadata_backend.md`: implementation notes

## Run

1. Install dependencies with `pip install -r requirements.txt`
2. Initialize PostgreSQL with `db/init.sql`
3. Start or restart the API with Docker:

```bash
cd /opt/db_api
docker compose build api
docker compose up -d api
docker compose ps
```

4. Open `http://localhost:8000/docs`
