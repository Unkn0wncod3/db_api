# DB API

Backend service for the DB project, built with FastAPI and PostgreSQL.

## Frontend (Separate Repository)

Frontend repository: https://github.com/Unkn0wncod3/DB_Frontend

The frontend and backend are fully separated by design:
- Independent repositories
- Independent deployment lifecycle
- API-first integration via HTTP endpoints

## What This Backend Does

This API provides:
- Structured data management on top of PostgreSQL
- Role-based access control (RBAC) for secure endpoint access
- Audit-oriented data retrieval for person-centric views
- PDF export of person dossiers for reporting and handover use cases

The service is intended as a standalone backend that can be consumed by any client (web, mobile, scripts) that can call HTTP endpoints.

## API as Interface Layer

This backend is the interface layer between frontend and database:
- The frontend never talks to PostgreSQL directly.
- The frontend sends HTTP requests to the API.
- The API validates input, enforces permissions, applies business rules, and then performs database operations.
- Responses are returned as JSON (or PDF for dossier export).

This keeps data access, security, and domain logic centralized in one backend codebase.

## System Architecture

The local stack runs with Docker Compose and contains three services:
- `db`: PostgreSQL 16 data layer
- `pgadmin`: Web UI for database inspection and admin workflows
- `api`: FastAPI application container

High-level request flow:
1. A client sends a request to the FastAPI service.
2. Authentication and role checks are applied.
3. The API performs reads/writes against PostgreSQL.
4. The response is returned as JSON (or PDF for dossier export routes).

## Predefined Data Schema

The project uses a predefined relational schema in `db/init.sql`.
All core entry types are standardized and stored in dedicated tables:

- `users`: application users, role, activation status, preferences
- `audit_logs`: request-level audit trail
- `persons`: core person records
- `notes`: notes linked to persons
- `platforms`: source platforms (for profile accounts)
- `profiles`: platform profiles/accounts
- `person_profile_map`: many-to-many person/profile links
- `vehicles`: vehicle records
- `activities`: timeline/activity entries linked to persons

Schema characteristics:
- `visibility_level` (`admin` or `user`) on domain tables for access filtering
- `created_at` and `updated_at` lifecycle timestamps
- Triggers to auto-maintain `updated_at`
- Constraints and indexes for data quality and query performance
- SQL views (`v_person_timeline`, `v_person_profiles`, `v_person_summary`) for read-optimized endpoint responses

## Endpoint Overview

Base URL (local): `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

### Health / Meta

- `GET /`
  - Basic health response (`{"status":"ok"}`).
- `GET /__routes`
  - Lists registered routes and methods.

### Auth

- `POST /auth/login`
  - Login with username/password and receive bearer token.
- `GET /auth/me`
  - Returns authenticated user profile.
- `PATCH /auth/me`
  - Updates own user fields (allowed self-service fields).

### Users (Admin)

- `GET /users`
  - List users (paginated).
- `POST /users`
  - Create user.
- `PATCH /users/{user_id}`
  - Update user fields.
- `PATCH /users/{user_id}/status`
  - Activate/deactivate user.
- `DELETE /users/{user_id}`
  - Delete user (self-delete blocked).

### Persons

- `GET /persons`
  - List persons with optional search/filter (`q`, `tag`, `limit`, `offset`).
- `GET /persons/{person_id}`
  - Get one person.
- `POST /persons`
  - Create person.
- `PATCH /persons/{person_id}`
  - Update person.
- `DELETE /persons/{person_id}`
  - Delete person.
- `GET /persons/{person_id}/dossier`
  - Consolidated person dossier JSON with relations/stats/audit.
- `GET /persons/{person_id}/dossier.pdf`
  - Same dossier as PDF export.

### Notes

- `GET /notes`
  - List notes.
- `GET /notes/{note_id}`
  - Get single note.
- `PATCH /notes/{note_id}`
  - Update note.
- `DELETE /notes/{note_id}`
  - Delete note.
- `GET /notes/by-person/{person_id}`
  - List notes for a person.
- `POST /notes/by-person/{person_id}`
  - Create note for a person.

### Platforms

- `GET /platforms`
  - List platforms.
- `GET /platforms/{platform_id}`
  - Get platform.
- `POST /platforms`
  - Create platform.
- `PATCH /platforms/{platform_id}`
  - Update platform.
- `DELETE /platforms/{platform_id}`
  - Delete platform.

### Profiles

- `GET /profiles`
  - List profiles (filterable by `platform_id`, `username`, paginated).
- `GET /profiles/{profile_id}`
  - Get profile.
- `POST /profiles`
  - Create profile.
- `PATCH /profiles/{profile_id}`
  - Update profile.
- `DELETE /profiles/{profile_id}`
  - Delete profile.

### Person Profile Links

- `GET /persons/{person_id}/profiles`
  - List linked profiles for person.
- `POST /persons/{person_id}/profiles`
  - Link profile to person (upsert behavior).
- `DELETE /persons/{person_id}/profiles/{profile_id}`
  - Unlink profile from person.

### Vehicles

- `GET /vehicles`
  - List vehicles.
- `GET /vehicles/{vehicle_id}`
  - Get vehicle.
- `POST /vehicles`
  - Create vehicle.
- `PATCH /vehicles/{vehicle_id}`
  - Update vehicle.
- `DELETE /vehicles/{vehicle_id}`
  - Delete vehicle.

### Activities

- `GET /activities`
  - List activities (filters: `person_id`, `activity_type`, `since`, plus pagination).
- `GET /activities/{activity_id}`
  - Get activity.
- `POST /activities`
  - Create activity.
- `PATCH /activities/{activity_id}`
  - Update activity.
- `DELETE /activities/{activity_id}`
  - Delete activity.

### Read-Optimized SQL Views

- `GET /views/person_timeline/{person_id}`
  - Timeline projection from SQL view.
- `GET /views/person_profiles`
  - Profiles projection for a person from SQL view.
- `GET /views/person_summary`
  - Person summary projection with aggregate counts.

### Stats

- `GET /stats/overview`
  - Returns entity totals, recent entries, and cache metadata.
  - Supports `force_refresh=true` to bypass in-process cache.

### Audit (Admin)

- `GET /audit/logs`
  - List audit logs with optional filters.
- `DELETE /audit/logs`
  - Clear audit logs.

## Authentication and Authorization

Before starting the API, define in `.env`:
- `AUTH_SECRET_KEY`
- `DEFAULT_ADMIN_USERNAME`
- `DEFAULT_ADMIN_PASSWORD`

Behavior:
- On first startup, a default **head admin** is created if no head admin exists.
- Clients obtain a signed access token via `POST /auth/login`.
- Protected endpoints require `Authorization: Bearer <token>`.

Role model:
- `head_admin`: Full control, including assigning admin/head-admin roles.
- `admin`: Full CRUD and user management, except assigning admin/head-admin roles.
- `editor`: Read access (except admin-only data), create/update non-user records, no delete, no user management.
- `user`: Read-only access to entries with user visibility.

Visibility enforcement:
- Admin roles can read `admin` and `user` entries.
- Non-admin roles can only read `user` visibility entries.
- Child entities inherit stricter parent visibility where required.

## Code Design

The codebase is organized by responsibility:
- `api/app/routers`: HTTP route handlers grouped by domain entity
- `api/app/schemas.py`: Pydantic request/response schemas and contracts
- `api/app/security.py`: token handling, password hashing, auth dependencies
- `api/app/visibility.py`: centralized visibility/RBAC SQL filtering helpers
- `api/app/services`: reusable business logic (users, dossiers, audit utilities)
- `api/app/middleware/audit.py`: request middleware that writes audit logs centrally
- `api/app/db.py`: database connection factory

Design principles used in this API:
- Clear separation of concerns (routing, validation, domain logic, persistence)
- Explicit role checks at route level (`require_role(...)`)
- Reusable SQL visibility rules to avoid duplicated permission logic
- Database-first consistency via schema constraints and triggers
- Auditability by default through middleware and event metadata hooks
- Read-heavy endpoints optimized with SQL views and lightweight caching (`/stats/overview`)

## Infrastructure and Runtime

Service endpoints (local):
- API base URL: http://localhost:8000
- OpenAPI docs: http://localhost:8000/docs
- pgAdmin: http://localhost:5050

The API container connects to PostgreSQL via the internal Docker network (`db:5432`).

## Operational Scripts

PowerShell helper scripts in `scripts/`:

- `.\scripts\start.ps1`
  - Starts the Docker Compose stack
  - Builds containers if needed
  - Shows service status
  - Runs `pytest` test suite

- `.\scripts\stop.ps1`
  - Stops and removes running Compose services

- `.\scripts\restart.ps1`
  - Stops services
  - Rebuilds `api` image without cache
  - Restarts the stack
  - Shows status
  - Runs tests

- `.\scripts\logs.ps1`
  - Streams logs of all Compose services

- `.\scripts\reset-db.ps1`
  - Executes `db/drop_all.sql` inside the DB container
  - Drops schema objects for a clean reset

- `.\scripts\init-db.ps1`
  - Executes `db/init.sql` inside the DB container
  - Recreates/initializes schema and base structures

- `.\scripts\example-data.ps1`
  - Executes `db/example_data.sql` inside the DB container
  - Seeds demo/example data

## Environment and Connection Details

pgAdmin credentials are loaded from `.env`:
- `PGADMIN_DEFAULT_EMAIL`
- `PGADMIN_DEFAULT_PASSWORD`

PostgreSQL profile (example for pgAdmin or external tools):
- Name: `Local Postgres`
- Host: `db` (from within Docker network) or `localhost` (from host machine)
- Port: `5432`
- Maintenance DB: `appdb`
- Username: `appuser`
- Password: `apppassword`

## Run It Yourself (Local Setup)

1. Clone this repository.
2. Create or update `.env` with all required database, pgAdmin, and auth values.
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the project:
   ```powershell
   .\scripts\start.ps1
   ```
5. Open the API docs and test endpoints:
   - http://localhost:8000/docs
6. Optional database lifecycle commands:
   - `.\scripts\init-db.ps1`
   - `.\scripts\reset-db.ps1`
   - `.\scripts\example-data.ps1`
7. Connect your frontend client to `http://localhost:8000`.

