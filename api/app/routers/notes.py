from fastapi import APIRouter, HTTPException
from ..db import get_connection
from ..schemas import NoteCreate

router = APIRouter(prefix="/notes", tags=["notes"])

@router.get("")
def list_notes():
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM notes ORDER BY id;")
        rows = cur.fetchall()
    return {"items": rows}

@router.get("/{note_id}")
def get_note(note_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM notes WHERE id=%s;", (note_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Note not found")
    return row

@router.delete("/{note_id}")
def delete_note(note_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM notes WHERE id=%s RETURNING id;", (note_id,))
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Note not found")
    return {"deleted": row["id"]}

@router.get("/by-person/{person_id}")
def list_person_notes(person_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM notes WHERE person_id=%s ORDER BY id DESC;", (person_id,))
        rows = cur.fetchall()
    return {"items": rows}

@router.post("/by-person/{person_id}", status_code=201)
def add_person_note(person_id: int, payload: NoteCreate):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO notes (person_id, title, text, pinned)
            VALUES (%s, %s, %s, %s)
            RETURNING *;
            """,
            (person_id, payload.title, payload.text, payload.pinned),
        )
        row = cur.fetchone()
        conn.commit()
    return row
