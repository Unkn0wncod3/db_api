from __future__ import annotations

from typing import Any, Dict, List, Optional

from psycopg.errors import UniqueViolation
from psycopg.types.json import Jsonb

from ..core.errors import ConflictError, NotFoundError
from ..db import get_connection


def _jsonb(value: Any):
    if value is None:
        return None
    return Jsonb(value)


class SchemaRepository:
    def list_schemas(self, *, include_inactive: bool = False) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM schemas"
        if not include_inactive:
            sql += " WHERE is_active IS TRUE"
        sql += " ORDER BY name, id"
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

    def get_schema(self, schema_id: int) -> Dict[str, Any]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM schemas WHERE id=%s;", (schema_id,))
            row = cur.fetchone()
        if not row:
            raise NotFoundError("Schema not found")
        return row

    def create_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with get_connection() as conn, conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO schemas (key, name, description, icon, is_active)
                    VALUES (%(key)s, %(name)s, %(description)s, %(icon)s, %(is_active)s)
                    RETURNING *;
                    """,
                    payload,
                )
            except UniqueViolation:
                conn.rollback()
                raise ConflictError("Schema key already exists")
            row = cur.fetchone()
            conn.commit()
        return row


class FieldRepository:
    def list_fields(self, schema_id: int, *, include_inactive: bool = False) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM fields WHERE schema_id=%s"
        params: List[Any] = [schema_id]
        if not include_inactive:
            sql += " AND is_active IS TRUE"
        sql += " ORDER BY sort_order, id"
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def create_field(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(payload)
        record["validation_json"] = _jsonb(record.get("validation_json") or {})
        record["settings_json"] = _jsonb(record.get("settings_json") or {})
        record["default_value"] = _jsonb(record.get("default_value"))
        with get_connection() as conn, conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO fields (
                        schema_id, key, label, description, data_type, is_required, is_unique,
                        default_value, sort_order, is_active, validation_json, settings_json
                    )
                    VALUES (
                        %(schema_id)s, %(key)s, %(label)s, %(description)s, %(data_type)s, %(is_required)s, %(is_unique)s,
                        %(default_value)s, %(sort_order)s, %(is_active)s, %(validation_json)s, %(settings_json)s
                    )
                    RETURNING *;
                    """,
                    record,
                )
            except UniqueViolation:
                conn.rollback()
                raise ConflictError("Field key already exists in schema")
            row = cur.fetchone()
            conn.commit()
        return row


class EntryRepository:
    def create_entry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(payload)
        record["data_json"] = Jsonb(record.get("data_json") or {})
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO entries (
                    schema_id, title, status, visibility_level, owner_id, created_by, data_json, archived_at, deleted_at
                )
                VALUES (
                    %(schema_id)s, %(title)s, %(status)s, %(visibility_level)s, %(owner_id)s, %(created_by)s, %(data_json)s, %(archived_at)s, %(deleted_at)s
                )
                RETURNING *;
                """,
                record,
            )
            row = cur.fetchone()
            conn.commit()
        row["data_json"] = row.get("data_json") or {}
        return row

    def get_entry(self, entry_id: int) -> Dict[str, Any]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM entries WHERE id=%s;", (entry_id,))
            row = cur.fetchone()
        if not row:
            raise NotFoundError("Entry not found")
        row["data_json"] = row.get("data_json") or {}
        return row

    def list_entries(self, *, schema_id: Optional[int] = None, owner_id: Optional[int] = None) -> List[Dict[str, Any]]:
        clauses = ["deleted_at IS NULL"]
        params: List[Any] = []
        if schema_id is not None:
            clauses.append("schema_id=%s")
            params.append(schema_id)
        if owner_id is not None:
            clauses.append("owner_id=%s")
            params.append(owner_id)
        sql = f"SELECT * FROM entries WHERE {' AND '.join(clauses)} ORDER BY updated_at DESC NULLS LAST, id DESC"
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        for row in rows:
            row["data_json"] = row.get("data_json") or {}
        return rows

    def update_entry(self, entry_id: int, fields: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(fields)
        if "data_json" in payload:
            payload["data_json"] = Jsonb(payload.get("data_json") or {})
        payload["entry_id"] = entry_id
        assignments = ", ".join(f"{key}=%({key})s" for key in fields)
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"UPDATE entries SET {assignments} WHERE id=%(entry_id)s RETURNING *;", payload)
            row = cur.fetchone()
            conn.commit()
        if not row:
            raise NotFoundError("Entry not found")
        row["data_json"] = row.get("data_json") or {}
        return row


class RelationRepository:
    def create_relation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(payload)
        record["metadata_json"] = Jsonb(record.get("metadata_json") or {})
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO entry_relations (from_entry_id, to_entry_id, relation_type, sort_order, metadata_json)
                VALUES (%(from_entry_id)s, %(to_entry_id)s, %(relation_type)s, %(sort_order)s, %(metadata_json)s)
                RETURNING *;
                """,
                record,
            )
            row = cur.fetchone()
            conn.commit()
        row["metadata_json"] = row.get("metadata_json") or {}
        return row

    def list_relations(self, entry_id: int) -> List[Dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM entry_relations
                WHERE from_entry_id=%s OR to_entry_id=%s
                ORDER BY sort_order, id;
                """,
                (entry_id, entry_id),
            )
            rows = cur.fetchall()
        for row in rows:
            row["metadata_json"] = row.get("metadata_json") or {}
        return rows


class HistoryRepository:
    def add_history(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(payload)
        record["old_data_json"] = _jsonb(record.get("old_data_json"))
        record["new_data_json"] = _jsonb(record.get("new_data_json"))
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO entry_history (
                    entry_id, changed_by, change_type, old_data_json, new_data_json,
                    old_visibility_level, new_visibility_level, comment
                )
                VALUES (
                    %(entry_id)s, %(changed_by)s, %(change_type)s, %(old_data_json)s, %(new_data_json)s,
                    %(old_visibility_level)s, %(new_visibility_level)s, %(comment)s
                )
                RETURNING *;
                """,
                record,
            )
            row = cur.fetchone()
            conn.commit()
        row["old_data_json"] = row.get("old_data_json") or {}
        row["new_data_json"] = row.get("new_data_json") or {}
        return row

    def list_history(self, entry_id: int) -> List[Dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM entry_history WHERE entry_id=%s ORDER BY changed_at DESC, id DESC;", (entry_id,))
            rows = cur.fetchall()
        for row in rows:
            row["old_data_json"] = row.get("old_data_json") or {}
            row["new_data_json"] = row.get("new_data_json") or {}
        return rows


class PermissionRepository:
    def create_permission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with get_connection() as conn, conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO entry_permissions (entry_id, subject_type, subject_id, permission, created_by)
                    VALUES (%(entry_id)s, %(subject_type)s, %(subject_id)s, %(permission)s, %(created_by)s)
                    RETURNING *;
                    """,
                    payload,
                )
            except UniqueViolation:
                conn.rollback()
                raise ConflictError("Permission already exists")
            row = cur.fetchone()
            conn.commit()
        return row

    def list_permissions(self, entry_id: int) -> List[Dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM entry_permissions WHERE entry_id=%s ORDER BY id;", (entry_id,))
            return cur.fetchall()


class AttachmentRepository:
    def create_attachment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with get_connection() as conn, conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO attachments (
                        entry_id, file_name, stored_path, mime_type, file_size, checksum, uploaded_by, description
                    )
                    VALUES (
                        %(entry_id)s, %(file_name)s, %(stored_path)s, %(mime_type)s, %(file_size)s, %(checksum)s, %(uploaded_by)s, %(description)s
                    )
                    RETURNING *;
                    """,
                    payload,
                )
            except UniqueViolation:
                conn.rollback()
                raise ConflictError("Attachment checksum already exists for entry")
            row = cur.fetchone()
            conn.commit()
        return row

    def list_attachments(self, entry_id: int) -> List[Dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM attachments WHERE entry_id=%s ORDER BY uploaded_at DESC, id DESC;", (entry_id,))
            return cur.fetchall()


def ensure_unique_field_value(schema_id: int, field_key: str, value: Any, *, exclude_entry_id: Optional[int] = None) -> None:
    clauses = [
        "schema_id=%s",
        "deleted_at IS NULL",
        "data_json ? %s",
        "jsonb_extract_path_text(data_json, %s) = %s",
    ]
    params: List[Any] = [schema_id, field_key, field_key, str(value)]
    if exclude_entry_id is not None:
        clauses.append("id <> %s")
        params.append(exclude_entry_id)
    sql = f"SELECT id FROM entries WHERE {' AND '.join(clauses)} LIMIT 1;"
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    if row:
        raise ConflictError(f"Field '{field_key}' must be unique")
