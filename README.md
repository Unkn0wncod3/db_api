
# DB Manager

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