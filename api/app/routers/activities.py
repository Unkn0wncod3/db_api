from typing import Optional, Any, List
from fastapi import APIRouter, HTTPException
from ..db import get_connection
from ..schemas import ActivityCreate

router = APIRouter(prefix="/activities", tags=["activities"])

@router.get("")
def list_activities(
    person_id: Optional[int] = None,
    activity_type: Optional[str] = None,
    since: Optional[str] = None,   # ISO-String; DB TIMESTAMPTZ cast
    limit: int = 100,
    offset: int = 0,
):
    sql = "SELECT * FROM activities WHERE 1=1"
    params: List[Any] = []
    if person_id:
        sql += " AND person_id=%s"
        params.append(person_id)
    if activity_type:
        sql += " AND activity_type=%s"
        params.append(activity_type)
    if since:
        sql += " AND occurred_at >= %s::timestamptz"
        params.append(since)
    sql += " ORDER BY occurred_at DESC LIMIT %s OFFSET %s"
    params += [limit, offset]
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return {"items": rows, "limit": limit, "offset": offset}

@router.post("", status_code=201)
def create_activity(payload: ActivityCreate):
    data = payload.model_dump()
    if not any([data.get("vehicle_id"), data.get("profile_id"), data.get("community_id"), data.get("item")]):
        raise HTTPException(400, "At least one of vehicle_id, profile_id, community_id or item must be provided.")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO activities (
                person_id, activity_type, occurred_at, vehicle_id, profile_id, community_id,
                item, notes, details, severity, source, ip_address, user_agent, geo_location, created_by
            ) VALUES (
                %(person_id)s, %(activity_type)s, %(occurred_at)s, %(vehicle_id)s, %(profile_id)s, %(community_id)s,
                %(item)s, %(notes)s, %(details)s, %(severity)s, %(source)s, %(ip_address)s, %(user_agent)s, %(geo_location)s, %(created_by)s
            ) RETURNING *;
            """,
            data,
        )
        row = cur.fetchone()
        conn.commit()
    return row
