from typing import Optional, Any, List

from fastapi import APIRouter, HTTPException
from psycopg.types.json import Jsonb

from ..db import get_connection
from ..schemas import ProfileCreate, ProfileUpdate

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("")
def list_profiles(
    platform_id: Optional[int] = None,
    username: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    sql = "SELECT * FROM profiles WHERE 1=1"
    params: List[Any] = []
    if platform_id:
        sql += " AND platform_id=%s"
        params.append(platform_id)
    if username:
        sql += " AND username ILIKE %s"
        params.append(f"%{username}%")
    sql += " ORDER BY id LIMIT %s OFFSET %s"
    params += [limit, offset]
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return {"items": rows, "limit": limit, "offset": offset}


@router.post("", status_code=201)
def create_profile(payload: ProfileCreate):
    data = payload.model_dump()
    if data.get("metadata") is not None:
        data["metadata"] = Jsonb(data["metadata"])

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO profiles (
                platform_id, username, external_id, display_name, url, status,
                language, region, is_verified, avatar_url, bio, metadata
            ) VALUES (
                %(platform_id)s, %(username)s, %(external_id)s, %(display_name)s, %(url)s, %(status)s,
                %(language)s, %(region)s, %(is_verified)s, %(avatar_url)s, %(bio)s, %(metadata)s
            ) RETURNING *;
            """,
            data,
        )
        row = cur.fetchone()
        conn.commit()
    return row


@router.patch("/{profile_id}")
def update_profile(profile_id: int, payload: ProfileUpdate):
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
    return row


@router.delete("/{profile_id}")
def delete_profile(profile_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM profiles WHERE id=%s RETURNING id;", (profile_id,))
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Profile not found")
    return {"deleted": row["id"]}
