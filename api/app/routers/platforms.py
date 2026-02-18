from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from ..db import get_connection
from ..roles import ADMIN_ROLES, EDITOR_ROLES, READ_ROLES
from ..schemas import PlatformCreate, PlatformUpdate
from ..security import require_role
from ..visibility import visibility_clause_for_role

router = APIRouter(
    prefix="/platforms",
    tags=["platforms"],
)

@router.get("")
def list_platforms(current_user: Dict = Depends(require_role(*READ_ROLES))):
    with get_connection() as conn, conn.cursor() as cur:
        sql = "SELECT * FROM platforms p WHERE 1=1"
        params = []
        clause, clause_params = visibility_clause_for_role(current_user["role"], alias="p")
        if clause:
            sql += f" AND {clause}"
            params.extend(clause_params)
        sql += " ORDER BY p.id"
        cur.execute(sql, params)
        rows = cur.fetchall()
    return {"items": rows}

@router.get("/{platform_id}")
def get_platform(platform_id: int, current_user: Dict = Depends(require_role(*READ_ROLES))):
    with get_connection() as conn, conn.cursor() as cur:
        sql = "SELECT * FROM platforms p WHERE p.id=%s"
        params = [platform_id]
        clause, clause_params = visibility_clause_for_role(current_user["role"], alias="p")
        if clause:
            sql += f" AND {clause}"
            params.extend(clause_params)
        cur.execute(sql, params)
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Platform not found")
    return row

@router.post("", status_code=201, dependencies=[Depends(require_role(*EDITOR_ROLES))])
def create_platform(payload: PlatformCreate):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO platforms (name, category, base_url, api_base_url, is_active, visibility_level)
            VALUES (%s,%s,%s,%s,%s,%s)
            RETURNING *;
            """,
            (
                payload.name,
                payload.category,
                payload.base_url,
                payload.api_base_url,
                payload.is_active,
                payload.visibility_level,
            ),
        )
        row = cur.fetchone()
        conn.commit()
    return row

@router.patch("/{platform_id}", dependencies=[Depends(require_role(*EDITOR_ROLES))])
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

@router.delete("/{platform_id}", dependencies=[Depends(require_role(*ADMIN_ROLES))])
def delete_platform(platform_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM platforms WHERE id=%s RETURNING id;", (platform_id,))
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Platform not found")
    return {"deleted": row["id"]}
