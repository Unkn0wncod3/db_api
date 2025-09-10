from fastapi import APIRouter
from ..db import get_connection

router = APIRouter(prefix="/views", tags=["views"])

@router.get("/person_timeline")
def view_person_timeline(person_id: int, limit: int = 100, offset: int = 0):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT *
            FROM v_person_timeline
            WHERE person_id=%s
            ORDER BY occurred_at DESC
            LIMIT %s OFFSET %s;
            """,
            (person_id, limit, offset),
        )
        rows = cur.fetchall()
    return {"items": rows, "limit": limit, "offset": offset}

@router.get("/person_profiles")
def view_person_profiles(person_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT * FROM v_person_profiles
            WHERE person_id=%s
            ORDER BY last_seen_at NULLS LAST;
            """,
            (person_id,),
        )
        rows = cur.fetchall()
    return {"items": rows}

@router.get("/person_summary")
def view_person_summary(limit: int = 100, offset: int = 0):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM v_person_summary ORDER BY person_id LIMIT %s OFFSET %s;",
            (limit, offset),
        )
        rows = cur.fetchall()
    return {"items": rows, "limit": limit, "offset": offset}
