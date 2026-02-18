from typing import Dict

from fastapi import APIRouter, Depends, Path, Query
from fastapi.encoders import jsonable_encoder

from ..db import get_connection as _get_connection
from ..roles import READ_ROLES
from ..security import require_role
from ..visibility import visibility_clause_for_role

router = APIRouter(
    prefix="/views",
    tags=["views"],
)

def get_conn():
    return _get_connection()

@router.get("/person_timeline/{person_id}")
def view_person_timeline(
    person_id: int = Path(..., ge=1),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn = Depends(get_conn),
    current_user: Dict = Depends(require_role(*READ_ROLES)),
):
    with conn.cursor() as cur:
        sql = """
        SELECT activity_id, occurred_at, person_id, person_name, activity_type,
               target, severity, source, geo_location, notes, details
        FROM public.v_person_timeline
        WHERE person_id = %s
        """
        params = [person_id]
        person_clause, person_params = visibility_clause_for_role(current_user["role"], column="person_visibility_level")
        if person_clause:
            sql += f" AND {person_clause}"
            params.extend(person_params)
        activity_clause, activity_params = visibility_clause_for_role(current_user["role"], column="activity_visibility_level")
        if activity_clause:
            sql += f" AND {activity_clause}"
            params.extend(activity_params)
        sql += " ORDER BY occurred_at DESC LIMIT %s OFFSET %s"
        params += [limit, offset]
        cur.execute(sql, params)
        rows = cur.fetchall()
        if rows and not isinstance(rows[0], dict):
            rows = [dict(r) for r in rows]
    return jsonable_encoder({"items": rows, "limit": limit, "offset": offset})


@router.get("/person_profiles")
def view_person_profiles(
    person_id: int,
    conn = Depends(get_conn),
    current_user: Dict = Depends(require_role(*READ_ROLES)),
    ):
    with conn.cursor() as cur:
        sql = """
        SELECT person_id, platform, username, display_name, status, last_seen_at, url
        FROM v_person_profiles
        WHERE person_id=%s
        """
        params = [person_id]
        for column in (
            "person_visibility_level",
            "profile_visibility_level",
            "platform_visibility_level",
            "link_visibility_level",
        ):
            clause, clause_params = visibility_clause_for_role(current_user["role"], column=column)
            if clause:
                sql += f" AND {clause}"
                params.extend(clause_params)
        sql += " ORDER BY last_seen_at NULLS LAST"
        cur.execute(sql, params)
        rows = cur.fetchall()
    return {"items": rows}

@router.get("/person_summary")
def view_person_summary(
    limit: int = 100, 
    offset: int = 0,
    conn = Depends(get_conn),
    current_user: Dict = Depends(require_role(*READ_ROLES)),
    ):
    with conn.cursor() as cur:
        sql = """
        SELECT person_id, person_name, email, status, profiles_count, activities_count, notes_count
        FROM v_person_summary
        WHERE 1=1
        """
        params: list = []
        clause, clause_params = visibility_clause_for_role(current_user["role"], column="visibility_level")
        if clause:
            sql += f" AND {clause}"
            params.extend(clause_params)
        sql += " ORDER BY person_id LIMIT %s OFFSET %s"
        params += [limit, offset]
        cur.execute(sql, params)
        rows = cur.fetchall()
    return {"items": rows, "limit": limit, "offset": offset}
