docker compose down
docker compose build --no-cache api
docker compose up -d --build
docker compose ps
python -m pytest -v