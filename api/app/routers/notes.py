from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from ..db import get_connection
from ..schemas import NoteCreate, NoteUpdate
from ..security import require_role
from ..visibility import inherit_visibility, visibility_clause_for_role

router = APIRouter(
    prefix="/notes",
    tags=["notes"],
)


def _append_visibility_filters(sql: str, params: list, role: str) -> tuple[str, list]:
    clause, clause_params = visibility_clause_for_role(role, alias="n")
    if clause:
        sql += f" AND {clause}"
        params.extend(clause_params)
    person_clause, person_params = visibility_clause_for_role(role, alias="p")
    if person_clause:
        sql += f" AND {person_clause}"
        params.extend(person_params)
    return sql, params


@router.get("")
def list_notes(current_user: Dict = Depends(require_role("user", "admin"))):
    with get_connection() as conn, conn.cursor() as cur:
        sql = """
        SELECT n.*
        FROM notes n
        JOIN persons p ON p.id = n.person_id
        WHERE 1=1
        """
        params: list = []
        sql, params = _append_visibility_filters(sql, params, current_user["role"])
        sql += " ORDER BY n.id"
        cur.execute(sql, params)
        rows = cur.fetchall()
    return {"items": rows}


@router.get("/{note_id}")
def get_note(note_id: int, current_user: Dict = Depends(require_role("user", "admin"))):
    with get_connection() as conn, conn.cursor() as cur:
        sql = """
        SELECT n.*
        FROM notes n
        JOIN persons p ON p.id = n.person_id
        WHERE n.id=%s
        """
        params = [note_id]
        sql, params = _append_visibility_filters(sql, params, current_user["role"])
        cur.execute(sql, params)
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Note not found")
    return row


@router.patch("/{note_id}", dependencies=[Depends(require_role("admin"))])
def update_note(note_id: int, payload: NoteUpdate):
    fields = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    if not fields:
        raise HTTPException(400, "No fields to update")
    set_sql = ", ".join([f"{column}=%({column})s" for column in fields])
    fields["note_id"] = note_id
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE notes SET {set_sql} WHERE id=%(note_id)s RETURNING *;",
            fields,
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Note not found")
    return row


@router.delete("/{note_id}", dependencies=[Depends(require_role("admin"))])
def delete_note(note_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM notes WHERE id=%s RETURNING id;", (note_id,))
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Note not found")
    return {"deleted": row["id"]}


@router.get("/by-person/{person_id}")
def list_person_notes(person_id: int, current_user: Dict = Depends(require_role("user", "admin"))):
    with get_connection() as conn, conn.cursor() as cur:
        sql = """
        SELECT n.*
        FROM notes n
        JOIN persons p ON p.id = n.person_id
        WHERE p.id=%s
        """
        params = [person_id]
        sql, params = _append_visibility_filters(sql, params, current_user["role"])
        sql += " ORDER BY n.id DESC"
        cur.execute(sql, params)
        rows = cur.fetchall()
    return {"items": rows}


@router.post("/by-person/{person_id}", status_code=201, dependencies=[Depends(require_role("admin"))])
def add_person_note(person_id: int, payload: NoteCreate):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT visibility_level FROM persons WHERE id=%s;", (person_id,))
        person = cur.fetchone()
        if not person:
            raise HTTPException(404, "Person not found")
        note_visibility = inherit_visibility(person["visibility_level"], payload.visibility_level)
        cur.execute(
            """
            INSERT INTO notes (person_id, title, text, pinned, visibility_level)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *;
            """,
            (person_id, payload.title, payload.text, payload.pinned, note_visibility),
        )
        row = cur.fetchone()
        conn.commit()
    return row
