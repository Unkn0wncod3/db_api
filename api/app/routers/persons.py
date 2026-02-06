from typing import Optional, Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg.types.json import Jsonb

from ..db import get_connection
from ..schemas import PersonCreate, PersonUpdate
from ..security import require_role
from ..visibility import visibility_clause_for_role

router = APIRouter(
    prefix="/persons",
    tags=["persons"],
)


@router.get("")
def list_persons(
    q: Optional[str] = Query(default=None, description="Suche in first_name/last_name/email"),
    tag: Optional[str] = Query(default=None, description="Filter by tag"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(require_role("user", "admin")),
):
    sql = """
    SELECT p.id, p.first_name, p.last_name, p.email, p.status, p.tags, p.created_at, p.updated_at, p.visibility_level
    FROM persons p
    WHERE 1=1
    """
    params: List[Any] = []
    if q:
        sql += " AND (first_name ILIKE %s OR last_name ILIKE %s OR email ILIKE %s)"
        like = f"%{q}%"
        params += [like, like, like]
    if tag:
        sql += " AND %s = ANY(tags)"
        params.append(tag)
    clause, clause_params = visibility_clause_for_role(current_user["role"], alias="p")
    if clause:
        sql += f" AND {clause}"
        params.extend(clause_params)
    sql += " ORDER BY id LIMIT %s OFFSET %s"
    params += [limit, offset]
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return {"items": rows, "limit": limit, "offset": offset}


@router.get("/{person_id}")
def get_person(person_id: int, current_user: Dict[str, Any] = Depends(require_role("user", "admin"))):
    with get_connection() as conn, conn.cursor() as cur:
        sql = "SELECT * FROM persons p WHERE p.id=%s"
        params: List[Any] = [person_id]
        clause, clause_params = visibility_clause_for_role(current_user["role"], alias="p")
        if clause:
            sql += f" AND {clause}"
            params.extend(clause_params)
        cur.execute(sql, params)
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Person not found")
    return row


@router.post("", status_code=201, dependencies=[Depends(require_role("admin"))])
def create_person(payload: PersonCreate):
    with get_connection() as conn, conn.cursor() as cur:
        data = payload.model_dump()
        if data.get("metadata") is not None:
            data["metadata"] = Jsonb(data["metadata"])

        cur.execute(
            """
            INSERT INTO persons (
                first_name,last_name,date_of_birth,gender,email,phone_number,
                address_line1,address_line2,postal_code,city,region_state,country,
                status,nationality,occupation,risk_level,tags,notes,metadata,visibility_level
            ) VALUES (
                %(first_name)s,%(last_name)s,%(date_of_birth)s,%(gender)s,%(email)s,%(phone_number)s,
                %(address_line1)s,%(address_line2)s,%(postal_code)s,%(city)s,%(region_state)s,%(country)s,
                %(status)s,%(nationality)s,%(occupation)s,%(risk_level)s,%(tags)s,%(notes)s,%(metadata)s,%(visibility_level)s
            ) RETURNING *;
            """,
            data,
        )
        row = cur.fetchone()
        conn.commit()
    return row


@router.patch("/{person_id}", dependencies=[Depends(require_role("admin"))])
def update_person(person_id: int, payload: PersonUpdate):
    fields = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    if not fields:
        raise HTTPException(400, "No fields to update")

    if fields.get("metadata") is not None:
        fields["metadata"] = Jsonb(fields["metadata"])

    set_sql = ", ".join([f"{k}=%({k})s" for k in fields.keys()])
    fields["person_id"] = person_id
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"UPDATE persons SET {set_sql} WHERE id=%(person_id)s RETURNING *;", fields)
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Person not found")
    return row


@router.delete("/{person_id}", dependencies=[Depends(require_role("admin"))])
def delete_person(person_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM persons WHERE id=%s RETURNING id;", (person_id,))
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Person not found")
    return {"deleted": row["id"]}
