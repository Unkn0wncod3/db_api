from datetime import date
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError
from .db import get_connection
import logging

logger = logging.getLogger("api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Postgres Docker Starter API")

# ---------- Schemas ----------
class FileCreate(BaseModel):
    title: str = Field(..., min_length=1)
    person_name: str = Field(..., min_length=1)
    date_of_birth: date  # ISO-Format "YYYY-MM-DD"

class FileOut(BaseModel):
    id: int
    title: str
    person_name: str
    date_of_birth: date

@app.get("/")
def root():
    return {"status": "ok"}


# ---------------- NOTES ----------------
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
            new_id = cur.fetchone()[0]
            conn.commit()
    return {"id": new_id, "title": title}

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
    return {"deleted": deleted[0]}

# ---------------- FILES ----------------
@app.get("/files")
def list_files():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, person_name, date_of_birth, created_at
                FROM files
                ORDER BY id;
            """)
            rows = cur.fetchall()
    return {"files": rows}

@app.get("/files/{file_id}")
def get_file(file_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, title, person_name, date_of_birth, created_at
            FROM files
            WHERE id = %s;
            """,
            (file_id,),
        )
        row = cur.fetchone()  # dict oder None
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    return row

@app.delete("/files/{file_id}")
def delete_file(file_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM files WHERE id = %s RETURNING id;", (file_id,))
        row = cur.fetchone()  # dict oder None
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    return {"deleted": row["id"]}

# ---------- Files: POST mit JSON-Body ----------
@app.post("/files", response_model=FileOut)
def add_file(payload: FileCreate):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO files (title, person_name, date_of_birth)
            VALUES (%s, %s, %s)
            RETURNING id, title, person_name, date_of_birth;
            """,
            (payload.title, payload.person_name, payload.date_of_birth),
        )
        row = cur.fetchone()  # dict
        conn.commit()
    if not row:
        raise HTTPException(status_code=500, detail="Insert did not return a row")
    return row  # passt zum response_model