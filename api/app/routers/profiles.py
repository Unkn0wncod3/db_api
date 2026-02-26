from typing import Optional, Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from psycopg.types.json import Jsonb

from ..db import get_connection
from ..roles import ADMIN_ROLES, EDITOR_ROLES, READ_ROLES
from ..schemas import ProfileCreate, ProfileUpdate
from ..security import require_role
from ..services import audit_logs
from ..visibility import visibility_clause_for_role

router = APIRouter(
    prefix="/profiles",
    tags=["profiles"],
)


@router.get("")
def list_profiles(
    platform_id: Optional[int] = None,
    username: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(require_role(*READ_ROLES)),
):
    sql = "SELECT * FROM profiles pr WHERE 1=1"
    params: List[Any] = []
    if platform_id:
        sql += " AND platform_id=%s"
        params.append(platform_id)
    if username:
        sql += " AND username ILIKE %s"
        params.append(f"%{username}%")
    clause, clause_params = visibility_clause_for_role(current_user["role"], alias="pr")
    if clause:
        sql += f" AND {clause}"
        params.extend(clause_params)
    sql += " ORDER BY id LIMIT %s OFFSET %s"
    params += [limit, offset]
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return {"items": rows, "limit": limit, "offset": offset}


@router.get("/{profile_id}")
def get_profile(profile_id: int, current_user: Dict[str, Any] = Depends(require_role(*READ_ROLES))):
    with get_connection() as conn, conn.cursor() as cur:
        sql = "SELECT * FROM profiles pr WHERE pr.id=%s"
        params = [profile_id]
        clause, clause_params = visibility_clause_for_role(current_user["role"], alias="pr")
        if clause:
            sql += f" AND {clause}"
            params.extend(clause_params)
        cur.execute(sql, params)
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Profile not found")
    return row

@router.post("", status_code=201, dependencies=[Depends(require_role(*EDITOR_ROLES))])
def create_profile(payload: ProfileCreate, request: Request):
    data = payload.model_dump()
    if data.get("metadata") is not None:
        data["metadata"] = Jsonb(data["metadata"])

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO profiles (
                platform_id, username, external_id, display_name, url, status,
                last_seen_at, language, region, is_verified, avatar_url, bio, metadata, visibility_level
            ) VALUES (
                %(platform_id)s, %(username)s, %(external_id)s, %(display_name)s, %(url)s, %(status)s,
                %(last_seen_at)s, %(language)s, %(region)s, %(is_verified)s, %(avatar_url)s, %(bio)s, %(metadata)s, %(visibility_level)s
            ) RETURNING *;
            """,
            data,
        )
        row = cur.fetchone()
        conn.commit()
    audit_logs.attach_request_metadata(
        request,
        event="profile_created",
        profile_id=row["id"],
        platform_id=row["platform_id"],
        username=row["username"],
    )
    return row


@router.patch("/{profile_id}", dependencies=[Depends(require_role(*EDITOR_ROLES))])
def update_profile(profile_id: int, payload: ProfileUpdate, request: Request):
    fields = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    if not fields:
        raise HTTPException(400, "No fields to update")

    if fields.get("metadata") is not None:
        fields["metadata"] = Jsonb(fields["metadata"])

    set_sql = ", ".join([f"{column}=%({column})s" for column in fields.keys()])
    fields["profile_id"] = profile_id
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE profiles SET {set_sql} WHERE id=%(profile_id)s RETURNING *;",
            fields,
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Profile not found")
    audit_logs.attach_request_metadata(
        request,
        event="profile_updated",
        profile_id=row["id"],
        username=row["username"],
        changed_fields=sorted(fields.keys()),
    )
    return row


@router.delete("/{profile_id}", dependencies=[Depends(require_role(*ADMIN_ROLES))])
def delete_profile(profile_id: int, request: Request):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM profiles WHERE id=%s RETURNING id, username, platform_id;", (profile_id,))
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Profile not found")
    audit_logs.attach_request_metadata(
        request,
        event="profile_deleted",
        profile_id=row["id"],
        username=row.get("username"),
        platform_id=row.get("platform_id"),
    )
    return {"deleted": row["id"]}
