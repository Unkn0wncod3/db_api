FROM python:3.11-slim

# System deps (optional: gcc for psycopg if not using binary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies first
COPY api/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# App-Code
COPY api/app /app/app

# Uvicorn Default-Port
EXPOSE 8000

# Start
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
