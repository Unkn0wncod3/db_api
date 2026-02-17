import os
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from psycopg.errors import UniqueViolation, UndefinedTable

from ..db import get_connection
from ..security import hash_password

USER_COLUMNS = "id, username, role, is_active, profile_picture_url, preferences, created_at, updated_at"
AUTH_COLUMNS = f"{USER_COLUMNS}, password_hash"


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
) -> Dict:
    password_hash = hash_password(password)
    preferences_payload = preferences or {}
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


def update_user(user_id: int, fields: Dict[str, Any]) -> Dict:
    if not fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    updates: Dict[str, Any] = {}
    for key in ("username", "role", "is_active", "profile_picture_url"):
        if key in fields:
            updates[key] = fields[key]

    if "preferences" in fields:
        updates["preferences"] = fields["preferences"] or {}

    if "password" in fields:
        updates["password_hash"] = hash_password(fields["password"])

    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT role, is_active FROM users WHERE id=%s;", (user_id,))
        existing = cur.fetchone()
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if existing["role"] == "admin":
            new_role = updates.get("role", existing["role"])
            new_active = updates.get("is_active", existing["is_active"])
            if new_role != "admin" or new_active is False:
                cur.execute("SELECT COUNT(*) AS c FROM users WHERE role='admin' AND id<>%s;", (user_id,))
                remaining = cur.fetchone()
                if not remaining or remaining["c"] == 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot remove the last admin user",
                    )

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


def delete_user(user_id: int) -> Dict:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT role FROM users WHERE id=%s;", (user_id,))
        existing = cur.fetchone()
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if existing["role"] == "admin":
            cur.execute("SELECT COUNT(*) AS c FROM users WHERE role='admin' AND id<>%s;", (user_id,))
            remaining = cur.fetchone()
            if not remaining or remaining["c"] == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete the last admin user")

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
            cur.execute("SELECT id FROM users WHERE role='admin' LIMIT 1;")
            if cur.fetchone():
                return

            password_hash = hash_password(password)
            cur.execute(
                f"""
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, 'admin')
                ON CONFLICT (username) DO NOTHING
                RETURNING {USER_COLUMNS};
                """,
                (username, password_hash),
            )
            created = cur.fetchone()
            conn.commit()
    except UndefinedTable:
        print("[auth] users table not found yet; skipping default admin bootstrap")
        return

    if created:
        print(f"[auth] Bootstrapped default admin user '{username}'")
