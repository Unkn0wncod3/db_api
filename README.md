
# DB API

### Preparations
pip install -r requirements.txt

# Scripts
### Start
.\scripts\start.ps1
### Stop
.\scripts\stop.ps1
### Restart
.\scripts\restart.ps1
### Show Logs
.\scripts\logs.ps1
### Reset DB
.\scripts\reset-db.ps1
### Initialize DB
.\scripts\init-db.ps1
### Add example data
.\scripts\example-data.ps1

## Connection:

pgAdmin4 (Web based): http://localhost:5050\
Login: PGADMIN_DEFAULT_EMAIL / PGADMIN_DEFAULT_PASSWORD aus .env

Name: Local Postgres\
Host: db (oder localhost)\
Port: 5432\
Maintenance DB: appdb\
Username: appuser\
Password: apppassword

API: http://localhost:8000\
OpenAPI Docs: http://localhost:8000/docs

## Authentication & Roles

- Set `AUTH_SECRET_KEY`, `DEFAULT_ADMIN_USERNAME`, and `DEFAULT_ADMIN_PASSWORD` in `.env` before starting the API.  
- On the first startup the service creates the default **head admin** if none exists; change the generated password afterwards via the `/users` endpoints.  
- Obtain an access token via `POST /auth/login` and send it as `Authorization: Bearer <token>` on subsequent requests.  
- Role rules:  
  - `head_admin`: full control including assigning other admin/head-admin users.  
  - `admin`: can perform every operation (read/write/delete, manage users) except granting admin/head-admin roles.  
  - `editor`: may read everything that is not `admin`-only, create/update non-user records, but cannot delete entries or manage users.  
  - `user`: read-only access to entries with `user` visibility.

## Person Dossiers

- `GET /persons/{id}/dossier`: returns a consolidated payload with the core person record, visibility metadata, recent profiles/notes/activities (defaults: 5 each), plus derived stats and audit info. Supports `profiles_limit`, `notes_limit`, and `activities_limit` query params as well as `If-None-Match`/`ETag` caching.
- `GET /persons/{id}/dossier.pdf`: same data rendered as a branded PDF and protected by the same RBAC + visibility checks. Returns `%PDF` bytes with `Content-Disposition: attachment`.
- PDF generation uses the pure-Python [`fpdf2`](https://pyfpdf.github.io/fpdf2/) library; no external binaries are required, but make sure this dependency is installed in environments that call the PDF route.
