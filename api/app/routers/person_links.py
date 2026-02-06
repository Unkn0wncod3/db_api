from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from ..db import get_connection
from ..schemas import LinkProfilePayload
from ..security import require_role
from ..visibility import visibility_clause_for_role

router = APIRouter(
    prefix="/persons",
    tags=["person-profile-links"],
)

@router.get("/{person_id}/profiles")
def list_person_profiles(person_id: int, current_user: Dict = Depends(require_role("user", "admin"))):
    with get_connection() as conn, conn.cursor() as cur:
        sql = """
        SELECT ppm.profile_id, pf.name AS platform, pr.username, pr.display_name, pr.status, pr.url
        FROM person_profile_map ppm
        JOIN persons per ON per.id = ppm.person_id
        JOIN profiles pr  ON pr.id = ppm.profile_id
        JOIN platforms pf ON pf.id = pr.platform_id
        WHERE ppm.person_id=%s
        """
        params = [person_id]
        for alias in ("ppm", "per", "pr", "pf"):
            clause, clause_params = visibility_clause_for_role(current_user["role"], alias=alias)
            if clause:
                sql += f" AND {clause}"
                params.extend(clause_params)
        sql += " ORDER BY pr.id"
        cur.execute(sql, params)
        rows = cur.fetchall()
    return {"items": rows}

@router.post("/{person_id}/profiles", status_code=201, dependencies=[Depends(require_role("admin"))])
def link_person_profile(person_id: int, payload: LinkProfilePayload):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO person_profile_map (person_id, profile_id, note, visibility_level)
            VALUES (%s, %s, %s, COALESCE(%s, 'user'))
            ON CONFLICT (person_id, profile_id) DO UPDATE
            SET note = EXCLUDED.note,
                visibility_level = COALESCE(EXCLUDED.visibility_level, person_profile_map.visibility_level)
            RETURNING *;
            """,
            (person_id, payload.profile_id, payload.note, payload.visibility_level),
        )
        row = cur.fetchone()
        conn.commit()
    return row

@router.delete("/{person_id}/profiles/{profile_id}", dependencies=[Depends(require_role("admin"))])
def unlink_person_profile(person_id: int, profile_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM person_profile_map WHERE person_id=%s AND profile_id=%s RETURNING person_id, profile_id;",
            (person_id, profile_id),
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Link not found")
    return {"deleted": row}
