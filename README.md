
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
- On the first startup the service creates the default admin if no admin exists; change the generated password afterwards via the `/users` endpoints.  
- Obtain an access token via `POST /auth/login` and send it as `Authorization: Bearer <token>` on subsequent requests.  
- Role rules: `user` may call only `GET` endpoints, while `admin` can also use every mutating (`POST/PATCH/DELETE`) endpoint plus the `/users` management routes.
