# db_manager
DB Manager

# Start
docker compose down
docker compose up -d
docker compose ps
docker compose logs -f db
docker compose exec -it db psql -U devuser -d devdb -c "\conninfo"

pgAdmin4: http://localhost:5050
Login: PGADMIN_DEFAULT_EMAIL / PGADMIN_DEFAULT_PASSWORD aus .env.

Connection:
Name: Local Postgres
Host: db (oder localhost)
Port: 5432
Maintenance DB: appdb
Username: appuser
Password: apppassword

API: http://localhost:8000
Liste: GET /notes → http://localhost:8000/notes
OpenAPI Docs: http://localhost:8000/docs

# ALT
# Python venv aktivieren & Pakete installieren
cd .\app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# Migration erzeugen & anwenden
alembic revision -m "init" --autogenerate
alembic upgrade head

# Sonstiges
YOUR_NEW_API_KEY: ltzvhyUbtpe2VMQedhtRTCh3hE4ZiAORPRzEHZYTvk0
NAME: admin-1

pip install -r requirements.txt

alembic revision -m "add email to users" --autogenerate
alembic upgrade head