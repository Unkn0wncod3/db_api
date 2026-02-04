from fastapi import APIRouter, Depends, HTTPException
from ..db import get_connection
from ..schemas import LinkProfilePayload
from ..security import require_role

router = APIRouter(
    prefix="/persons",
    tags=["person-profile-links"],
    dependencies=[Depends(require_role("user", "admin"))],
)

@router.get("/{person_id}/profiles")
def list_person_profiles(person_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT ppm.profile_id, pf.name AS platform, pr.username, pr.display_name, pr.status, pr.url
            FROM person_profile_map ppm
            JOIN profiles pr  ON pr.id = ppm.profile_id
            JOIN platforms pf ON pf.id = pr.platform_id
            WHERE ppm.person_id=%s
            ORDER BY pr.id;
            """,
            (person_id,),
        )
        rows = cur.fetchall()
    return {"items": rows}

@router.post("/{person_id}/profiles", status_code=201, dependencies=[Depends(require_role("admin"))])
def link_person_profile(person_id: int, payload: LinkProfilePayload):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO person_profile_map (person_id, profile_id, note)
            VALUES (%s, %s, %s)
            ON CONFLICT (person_id, profile_id) DO UPDATE SET note = EXCLUDED.note
            RETURNING *;
            """,
            (person_id, payload.profile_id, payload.note),
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
