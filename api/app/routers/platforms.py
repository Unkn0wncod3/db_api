from fastapi import APIRouter, HTTPException
from ..db import get_connection
from ..schemas import PlatformCreate, PlatformUpdate

router = APIRouter(prefix="/platforms", tags=["platforms"])

@router.get("")
def list_platforms():
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM platforms ORDER BY id;")
        rows = cur.fetchall()
    return {"items": rows}

@router.get("/{platform_id}")
def get_platform(platform_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM platforms WHERE id=%s", (platform_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Platform not found")
    return row

@router.post("", status_code=201)
def create_platform(payload: PlatformCreate):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO platforms (name, category, base_url, api_base_url, is_active)
            VALUES (%s,%s,%s,%s,%s)
            RETURNING *;
            """,
            (payload.name, payload.category, payload.base_url, payload.api_base_url, payload.is_active),
        )
        row = cur.fetchone()
        conn.commit()
    return row

@router.patch("/{platform_id}")
def update_platform(platform_id: int, payload: PlatformUpdate):
    fields = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    if not fields:
        raise HTTPException(400, "No fields to update")
    set_sql = ", ".join([f"{column}=%({column})s" for column in fields.keys()])
    fields["platform_id"] = platform_id
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE platforms SET {set_sql} WHERE id=%(platform_id)s RETURNING *;",
            fields,
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Platform not found")
    return row

@router.delete("/{platform_id}")
def delete_platform(platform_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM platforms WHERE id=%s RETURNING id;", (platform_id,))
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Platform not found")
    return {"deleted": row["id"]}
