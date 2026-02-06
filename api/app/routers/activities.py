from typing import Optional, Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException
from psycopg.types.json import Jsonb

from ..db import get_connection
from ..schemas import ActivityCreate, ActivityUpdate
from ..security import require_role
from ..visibility import visibility_clause_for_role

router = APIRouter(
    prefix="/activities",
    tags=["activities"],
)


@router.get("")
def list_activities(
    person_id: Optional[int] = None,
    activity_type: Optional[str] = None,
    since: Optional[str] = None,  # ISO-String; DB TIMESTAMPTZ cast
    limit: int = 100,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(require_role("user", "admin")),
):
    sql = """
    SELECT a.*
    FROM activities a
    JOIN persons p ON p.id = a.person_id
    WHERE 1=1
    """
    params: List[Any] = []
    if person_id:
        sql += " AND a.person_id=%s"
        params.append(person_id)
    if activity_type:
        sql += " AND a.activity_type=%s"
        params.append(activity_type)
    if since:
        sql += " AND a.occurred_at >= %s::timestamptz"
        params.append(since)
    activity_clause, activity_params = visibility_clause_for_role(current_user["role"], alias="a")
    if activity_clause:
        sql += f" AND {activity_clause}"
        params.extend(activity_params)
    person_clause, person_params = visibility_clause_for_role(current_user["role"], alias="p")
    if person_clause:
        sql += f" AND {person_clause}"
        params.extend(person_params)
    sql += " ORDER BY occurred_at DESC LIMIT %s OFFSET %s"
    params += [limit, offset]
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return {"items": rows, "limit": limit, "offset": offset}


@router.get("/{activity_id}")
def get_activity(activity_id: int, current_user: Dict[str, Any] = Depends(require_role("user", "admin"))):
    with get_connection() as conn, conn.cursor() as cur:
        sql = """
        SELECT a.*
        FROM activities a
        JOIN persons p ON p.id = a.person_id
        WHERE a.id=%s
        """
        params = [activity_id]
        activity_clause, activity_params = visibility_clause_for_role(current_user["role"], alias="a")
        if activity_clause:
            sql += f" AND {activity_clause}"
            params.extend(activity_params)
        person_clause, person_params = visibility_clause_for_role(current_user["role"], alias="p")
        if person_clause:
            sql += f" AND {person_clause}"
            params.extend(person_params)
        cur.execute(sql, params)
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Activity not found")
    return row

@router.post("", status_code=201, dependencies=[Depends(require_role("admin"))])
def create_activity(payload: ActivityCreate):
    data = payload.model_dump()
    if not any([data.get("vehicle_id"), data.get("profile_id"), data.get("community_id"), data.get("item")]):
        raise HTTPException(400, "At least one of vehicle_id, profile_id, community_id or item must be provided.")

    if data.get("details") is not None:
        data["details"] = Jsonb(data["details"])

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO activities (
                person_id, activity_type, occurred_at, vehicle_id, profile_id, community_id,
                item, notes, details, severity, source, ip_address, user_agent, geo_location, created_by, visibility_level
            ) VALUES (
                %(person_id)s, %(activity_type)s, %(occurred_at)s, %(vehicle_id)s, %(profile_id)s, %(community_id)s,
                %(item)s, %(notes)s, %(details)s, %(severity)s, %(source)s, %(ip_address)s, %(user_agent)s, %(geo_location)s, %(created_by)s, %(visibility_level)s
            ) RETURNING *;
            """,
            data,
        )
        row = cur.fetchone()
        conn.commit()
    return row


@router.patch("/{activity_id}", dependencies=[Depends(require_role("admin"))])
def update_activity(activity_id: int, payload: ActivityUpdate):
    fields = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    if not fields:
        raise HTTPException(400, "No fields to update")

    if fields.get("details") is not None:
        fields["details"] = Jsonb(fields["details"])

    set_sql = ", ".join([f"{column}=%({column})s" for column in fields])
    fields["activity_id"] = activity_id
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE activities SET {set_sql} WHERE id=%(activity_id)s RETURNING *;",
            fields,
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Activity not found")
    return row


@router.delete("/{activity_id}", dependencies=[Depends(require_role("admin"))])
def delete_activity(activity_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM activities WHERE id=%s RETURNING id;", (activity_id,))
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Activity not found")
    return {"deleted": row["id"]}
