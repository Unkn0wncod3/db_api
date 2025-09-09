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

from fastapi import HTTPException

@app.get("/notes/{note_id}")
def get_note(note_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, created_at FROM notes WHERE id = %s;", (note_id,))
            note = cur.fetchone()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@app.delete("/notes/{note_id}")
def delete_note(note_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM notes WHERE id = %s RETURNING id;", (note_id,))
            deleted = cur.fetchone()
            conn.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"deleted": deleted["id"]}