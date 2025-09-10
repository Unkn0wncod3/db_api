from fastapi import APIRouter
from ..db import get_connection
from ..schemas import PlatformCreate

router = APIRouter(prefix="/platforms", tags=["platforms"])

@router.get("")
def list_platforms():
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM platforms ORDER BY id;")
        rows = cur.fetchall()
    return {"items": rows}

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
