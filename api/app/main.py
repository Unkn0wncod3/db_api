from fastapi import FastAPI
from .db import get_connection

app = FastAPI(title="Postgres Docker Starter API")

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/notes")
def list_notes():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, created_at FROM notes ORDER BY id;")
            rows = cur.fetchall()
    return {"notes": rows}

@app.post("/notes")
def add_note(title: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO notes (title) VALUES (%s) RETURNING id;", (title,))
            new_id = cur.fetchone()["id"]
            conn.commit()
    return {"id": new_id, "title": title}
