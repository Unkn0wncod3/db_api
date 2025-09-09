
# DB Manager

pip install -r requirements.txt

docker compose down\
docker compose up -d\
docker compose ps\
docker compose logs -f db\
docker compose exec -it db psql -U devuser -d devdb -c "\conninfo"

## Connection:

pgAdmin4: http://localhost:5050\
Login: PGADMIN_DEFAULT_EMAIL / PGADMIN_DEFAULT_PASSWORD aus .env

Name: Local Postgres\
Host: db (oder localhost)\
Port: 5432\
Maintenance DB: appdb\
Username: appuser\
Password: apppassword

API: http://localhost:8000
Liste: GET /notes → http://localhost:8000/notes
OpenAPI Docs: http://localhost:8000/docs

# Reset DB
docker compose down -v\
stoppt Container und löscht Volumes (Daten!)\
\
docker compose up -d\
startet neu, init.sql wird ausgeführt



# Migration erzeugen & anwenden
alembic revision -m "init" --autogenerate\
alembic upgrade head

# Sonstiges
alembic revision -m "add email to users" --autogenerate\
alembic upgrade head