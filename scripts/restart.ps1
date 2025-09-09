docker compose down
docker compose build --no-cache api
docker compose up -d
docker compose ps