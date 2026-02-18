import os
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from psycopg.errors import UniqueViolation, UndefinedTable
from psycopg.types.json import Jsonb

from ..db import get_connection
from ..roles import ADMIN_ROLE_SET, ROLE_ADMIN, ROLE_HEAD_ADMIN
from ..security import hash_password

SELF_SERVICE_FIELDS = {"username", "password", "profile_picture_url", "preferences"}

USER_COLUMNS = "id, username, role, is_active, profile_picture_url, preferences, created_at, updated_at"
AUTH_COLUMNS = f"{USER_COLUMNS}, password_hash"


def _ensure_actor_is_admin(actor_role: Optional[str]) -> None:
    if actor_role is None:
        return
    if actor_role not in ADMIN_ROLE_SET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


def _ensure_actor_can_assign_role(actor_role: Optional[str], target_role: str) -> None:
    if actor_role is None:
        return
    _ensure_actor_is_admin(actor_role)
    if target_role in ADMIN_ROLE_SET and actor_role != ROLE_HEAD_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only head admins may assign admin roles",
        )


def _ensure_actor_can_manage_target(actor_role: Optional[str], target_role: str, *, is_self: bool) -> None:
    if target_role == ROLE_HEAD_ADMIN and actor_role != ROLE_HEAD_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only head admins may manage other head admins",
        )
    if not is_self:
        _ensure_actor_is_admin(actor_role)


def _assert_remaining_admin(cur, exclude_user_id: int) -> None:
    cur.execute(
        "SELECT COUNT(*) AS c FROM users WHERE role IN (%s, %s) AND is_active IS NOT FALSE AND id<>%s;",
        (ROLE_HEAD_ADMIN, ROLE_ADMIN, exclude_user_id),
    )
    remaining = cur.fetchone()
    if not remaining or remaining["c"] == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the last admin-level user",
        )


def _assert_remaining_head_admin(cur, exclude_user_id: int) -> None:
    cur.execute(
        "SELECT COUNT(*) AS c FROM users WHERE role=%s AND is_active IS NOT FALSE AND id<>%s;",
        (ROLE_HEAD_ADMIN, exclude_user_id),
    )
    remaining = cur.fetchone()
    if not remaining or remaining["c"] == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the last head admin user",
        )


def _row_to_public(row: Dict) -> Dict:
    if not row:
        return {}
    data = {key: row.get(key) for key in ["id", "username", "role", "is_active", "profile_picture_url", "preferences", "created_at", "updated_at"]}
    if data.get("preferences") is None:
        data["preferences"] = {}
    return data


def get_user_by_username(username: str, *, include_secret: bool = False) -> Optional[Dict]:
    columns = AUTH_COLUMNS if include_secret else USER_COLUMNS
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT {columns} FROM users WHERE username=%s;", (username,))
        row = cur.fetchone()
    if row and row.get("preferences") is None:
        row["preferences"] = {}
    return row


def get_user_by_id(user_id: int, *, include_secret: bool = False) -> Optional[Dict]:
    columns = AUTH_COLUMNS if include_secret else USER_COLUMNS
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT {columns} FROM users WHERE id=%s;", (user_id,))
        row = cur.fetchone()
    if row and row.get("preferences") is None:
        row["preferences"] = {}
    return row


def list_users(limit: int = 50, offset: int = 0) -> Dict[str, List[Dict]]:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT {USER_COLUMNS} FROM users ORDER BY id LIMIT %s OFFSET %s;",
            (limit, offset),
        )
        rows = cur.fetchall()
    for row in rows:
        if row.get("preferences") is None:
            row["preferences"] = {}
    return {"items": rows, "limit": limit, "offset": offset}


def create_user(
    username: str,
    password: str,
    role: str,
    profile_picture_url: Optional[str] = None,
    preferences: Optional[Dict[str, Any]] = None,
    *,
    acting_user: Optional[Dict[str, Any]] = None,
) -> Dict:
    actor_role = (acting_user or {}).get("role")
    _ensure_actor_is_admin(actor_role)
    _ensure_actor_can_assign_role(actor_role, role)
    password_hash = hash_password(password)
    preferences_payload = preferences or {}
    if preferences_payload is not None:
        preferences_payload = Jsonb(preferences_payload)
    with get_connection() as conn, conn.cursor() as cur:
        try:
            cur.execute(
                f"""
                INSERT INTO users (username, password_hash, role, profile_picture_url, preferences)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING {USER_COLUMNS};
                """,
                (username, password_hash, role, profile_picture_url, preferences_payload),
            )
        except UniqueViolation:
            conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
        user = cur.fetchone()
        conn.commit()
    return user


def update_user(user_id: int, fields: Dict[str, Any], *, acting_user: Optional[Dict[str, Any]] = None) -> Dict:
    if not fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    actor = acting_user or {}
    actor_role = actor.get("role")
    is_self_update = actor.get("id") == user_id if actor.get("id") is not None else False

    if acting_user is not None and actor_role not in ADMIN_ROLE_SET:
        if not is_self_update:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        disallowed = set(fields.keys()) - SELF_SERVICE_FIELDS
        if disallowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You cannot update the following fields: {', '.join(sorted(disallowed))}",
            )

    updates: Dict[str, Any] = {}
    for key in ("username", "role", "is_active", "profile_picture_url"):
        if key in fields:
            updates[key] = fields[key]

    if "preferences" in fields:
        pref_value = fields["preferences"] or {}
        updates["preferences"] = Jsonb(pref_value)

    if "password" in fields:
        updates["password_hash"] = hash_password(fields["password"])

    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT role, is_active FROM users WHERE id=%s;", (user_id,))
        existing = cur.fetchone()
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if acting_user is not None:
            _ensure_actor_can_manage_target(actor_role, existing["role"], is_self=is_self_update)
            if "role" in updates:
                _ensure_actor_can_assign_role(actor_role, updates["role"])

        new_role = updates.get("role", existing["role"])
        new_active = updates.get("is_active", existing["is_active"])

        removing_admin_role = existing["role"] in ADMIN_ROLE_SET and (
            new_role not in ADMIN_ROLE_SET or new_active is False
        )
        removing_head_admin = existing["role"] == ROLE_HEAD_ADMIN and (
            new_role != ROLE_HEAD_ADMIN or new_active is False
        )

        if removing_admin_role:
            _assert_remaining_admin(cur, user_id)
        if removing_head_admin:
            _assert_remaining_head_admin(cur, user_id)

        set_clause = ", ".join(f"{column}=%({column})s" for column in updates)
        updates["user_id"] = user_id

        try:
            cur.execute(
                f"UPDATE users SET {set_clause} WHERE id=%(user_id)s RETURNING {USER_COLUMNS};",
                updates,
            )
        except UniqueViolation:
            conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

        updated = cur.fetchone()
        conn.commit()

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if updated.get("preferences") is None:
        updated["preferences"] = {}
    return updated


def delete_user(user_id: int, *, acting_user: Optional[Dict[str, Any]] = None) -> Dict:
    actor = acting_user or {}
    actor_role = actor.get("role")
    is_self_delete = acting_user is not None and actor.get("id") == user_id
    if is_self_delete:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Users cannot delete themselves")

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT role FROM users WHERE id=%s;", (user_id,))
        existing = cur.fetchone()
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if acting_user is not None:
            _ensure_actor_can_manage_target(actor_role, existing["role"], is_self=False)

        if existing["role"] in ADMIN_ROLE_SET:
            _assert_remaining_admin(cur, user_id)
        if existing["role"] == ROLE_HEAD_ADMIN:
            _assert_remaining_head_admin(cur, user_id)

        cur.execute(
            f"DELETE FROM users WHERE id=%s RETURNING {USER_COLUMNS};",
            (user_id,),
        )
        deleted = cur.fetchone()
        conn.commit()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if deleted.get("preferences") is None:
        deleted["preferences"] = {}
    return deleted


def ensure_default_admin() -> None:
    username = os.environ.get("DEFAULT_ADMIN_USERNAME")
    password = os.environ.get("DEFAULT_ADMIN_PASSWORD")
    if not username or not password:
        return

    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE role=%s LIMIT 1;", (ROLE_HEAD_ADMIN,))
            if cur.fetchone():
                return

            password_hash = hash_password(password)
            cur.execute(
                f"""
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                RETURNING {USER_COLUMNS};
                """,
                (username, password_hash, ROLE_HEAD_ADMIN),
            )
            created = cur.fetchone()
            conn.commit()
    except UndefinedTable:
        print("[auth] users table not found yet; skipping default admin bootstrap")
        return

    if created:
        print(f"[auth] Bootstrapped default head admin user '{username}'")
