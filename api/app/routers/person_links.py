from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request

from ..db import get_connection
from ..roles import ADMIN_ROLES, EDITOR_ROLES, READ_ROLES
from ..schemas import LinkProfilePayload
from ..security import require_role
from ..services import audit_logs
from ..visibility import inherit_visibility, visibility_clause_for_role

router = APIRouter(
    prefix="/persons",
    tags=["person-profile-links"],
)

@router.get("/{person_id}/profiles")
def list_person_profiles(person_id: int, current_user: Dict = Depends(require_role(*READ_ROLES))):
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

@router.post("/{person_id}/profiles", status_code=201, dependencies=[Depends(require_role(*EDITOR_ROLES))])
def link_person_profile(person_id: int, payload: LinkProfilePayload, request: Request):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT visibility_level FROM persons WHERE id=%s;", (person_id,))
        person = cur.fetchone()
        if not person:
            raise HTTPException(404, "Person not found")
        link_visibility = inherit_visibility(person["visibility_level"], payload.visibility_level)
        cur.execute(
            """
            INSERT INTO person_profile_map (person_id, profile_id, note, visibility_level)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (person_id, profile_id) DO UPDATE
            SET note = EXCLUDED.note,
                visibility_level = EXCLUDED.visibility_level
            RETURNING *;
            """,
            (person_id, payload.profile_id, payload.note, link_visibility),
        )
        row = cur.fetchone()
        conn.commit()
    audit_logs.attach_request_metadata(
        request,
        event="profile_linked",
        person_id=row["person_id"],
        profile_id=row["profile_id"],
        note=row.get("note"),
    )
    return row

@router.delete("/{person_id}/profiles/{profile_id}", dependencies=[Depends(require_role(*ADMIN_ROLES))])
def unlink_person_profile(person_id: int, profile_id: int, request: Request):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM person_profile_map WHERE person_id=%s AND profile_id=%s RETURNING person_id, profile_id;",
            (person_id, profile_id),
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Link not found")
    audit_logs.attach_request_metadata(
        request,
        event="profile_unlinked",
        person_id=row["person_id"],
        profile_id=row["profile_id"],
    )
    return {"deleted": row}
