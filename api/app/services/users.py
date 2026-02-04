import os
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from psycopg.errors import UniqueViolation, UndefinedTable

from ..db import get_connection
from ..security import hash_password

USER_COLUMNS = "id, username, role, is_active, created_at, updated_at"
AUTH_COLUMNS = f"{USER_COLUMNS}, password_hash"


def _row_to_public(row: Dict) -> Dict:
    return {key: row.get(key) for key in ["id", "username", "role", "is_active", "created_at", "updated_at"]}


def get_user_by_username(username: str, *, include_secret: bool = False) -> Optional[Dict]:
    columns = AUTH_COLUMNS if include_secret else USER_COLUMNS
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT {columns} FROM users WHERE username=%s;", (username,))
        row = cur.fetchone()
    return row


def get_user_by_id(user_id: int, *, include_secret: bool = False) -> Optional[Dict]:
    columns = AUTH_COLUMNS if include_secret else USER_COLUMNS
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT {columns} FROM users WHERE id=%s;", (user_id,))
        row = cur.fetchone()
    return row


def list_users(limit: int = 50, offset: int = 0) -> Dict[str, List[Dict]]:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT {USER_COLUMNS} FROM users ORDER BY id LIMIT %s OFFSET %s;",
            (limit, offset),
        )
        rows = cur.fetchall()
    return {"items": rows, "limit": limit, "offset": offset}


def create_user(username: str, password: str, role: str) -> Dict:
    password_hash = hash_password(password)
    with get_connection() as conn, conn.cursor() as cur:
        try:
            cur.execute(
                f"""
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, %s)
                RETURNING {USER_COLUMNS};
                """,
                (username, password_hash, role),
            )
        except UniqueViolation:
            conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
        user = cur.fetchone()
        conn.commit()
    return user


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
