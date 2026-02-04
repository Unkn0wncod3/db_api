from fastapi import APIRouter, Depends, Path, Query
from fastapi.encoders import jsonable_encoder
from ..db import get_connection as _get_connection
from ..security import require_role

router = APIRouter(
    prefix="/views",
    tags=["views"],
    dependencies=[Depends(require_role("user", "admin"))],
)

def get_conn():
    return _get_connection()

@router.get("/person_timeline/{person_id}")
def view_person_timeline(
    person_id: int = Path(..., ge=1),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn = Depends(get_conn),
):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT *
            FROM public.v_person_timeline
            WHERE person_id = %s
            ORDER BY occurred_at DESC
            LIMIT %s OFFSET %s;
            """,
            (person_id, limit, offset),
        )
        rows = cur.fetchall()
        if rows and not isinstance(rows[0], dict):
            rows = [dict(r) for r in rows]
    return jsonable_encoder({"items": rows, "limit": limit, "offset": offset})


@router.get("/person_profiles")
def view_person_profiles(
    person_id: int,
    conn = Depends(get_conn),
    ):
    with conn.cursor() as cur:
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
def view_person_summary(
    limit: int = 100, 
    offset: int = 0,
    conn = Depends(get_conn),
    ):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM v_person_summary ORDER BY person_id LIMIT %s OFFSET %s;",
            (limit, offset),
        )
        rows = cur.fetchall()
    return {"items": rows, "limit": limit, "offset": offset}
