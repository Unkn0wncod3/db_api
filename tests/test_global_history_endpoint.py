from datetime import datetime, timedelta, timezone

from api.app.db import get_connection
from api.app.security import create_access_token
from psycopg.types.json import Jsonb


def _ensure_users() -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (id, username, password_hash, role, is_active, preferences)
            VALUES
                (999, 'history_manager', 'test-hash', 'manager', TRUE, '{}'::jsonb),
                (1000, 'history_reader', 'test-hash', 'reader', TRUE, '{}'::jsonb)
            ON CONFLICT (id) DO UPDATE SET
                username = EXCLUDED.username,
                password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role,
                is_active = EXCLUDED.is_active,
                preferences = EXCLUDED.preferences;
            """
        )
        conn.commit()


def _auth_headers() -> dict[str, str]:
    token = create_access_token({"id": 999, "role": "manager"})
    return {"Authorization": f"Bearer {token}"}


def test_global_history_endpoint_is_paginated_filterable_and_access_filtered(client):
    _ensure_users()
    auth_headers = _auth_headers()

    schema_resp = client.post(
        "/schemas",
        headers={"X-Test-Role": "manager"},
        json={
            "key": "history_case",
            "name": "History Case",
            "description": "Schema for global history test",
            "icon": "clock-3",
            "is_active": True,
        },
    )
    assert schema_resp.status_code == 201
    schema_id = schema_resp.json()["id"]

    now = datetime.now(timezone.utc)
    own_changed_at = now
    granted_changed_at = now - timedelta(hours=1)
    hidden_changed_at = now - timedelta(hours=2)

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO entries (schema_id, title, status, visibility_level, owner_id, created_by, data_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (schema_id, "Own Visible Entry", "open", "private", 999, 999, Jsonb({"summary": "own"})),
        )
        own_entry_id = cur.fetchone()["id"]

        cur.execute(
            """
            INSERT INTO entries (schema_id, title, status, visibility_level, owner_id, created_by, data_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (schema_id, "Granted Entry", "open", "private", 1000, 1000, Jsonb({"summary": "granted"})),
        )
        granted_entry_id = cur.fetchone()["id"]

        cur.execute(
            """
            INSERT INTO entry_permissions (entry_id, subject_type, subject_id, permission, created_by)
            VALUES (%s, 'user', '999', 'view_history', %s);
            """,
            (granted_entry_id, 1000),
        )

        cur.execute(
            """
            INSERT INTO entries (schema_id, title, status, visibility_level, owner_id, created_by, data_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (schema_id, "Hidden Entry", "open", "private", 1000, 1000, Jsonb({"summary": "hidden"})),
        )
        hidden_entry_id = cur.fetchone()["id"]

        cur.execute(
            """
            INSERT INTO entry_history (
                entry_id, changed_by, change_type, old_data_json, new_data_json,
                old_visibility_level, new_visibility_level, changed_at, comment
            )
            VALUES (%s, %s, 'updated', %s, %s, 'internal', 'private', %s, %s);
            """,
            (
                own_entry_id,
                999,
                Jsonb({"summary": "old own"}),
                Jsonb({"summary": "new own"}),
                own_changed_at,
                "Own update",
            ),
        )
        cur.execute(
            """
            INSERT INTO entry_history (
                entry_id, changed_by, change_type, old_data_json, new_data_json,
                old_visibility_level, new_visibility_level, changed_at, comment
            )
            VALUES (%s, %s, 'updated', %s, %s, 'private', 'private', %s, %s);
            """,
            (
                granted_entry_id,
                1000,
                Jsonb({"summary": "old granted"}),
                Jsonb({"summary": "new granted"}),
                granted_changed_at,
                "Granted update",
            ),
        )
        cur.execute(
            """
            INSERT INTO entry_history (
                entry_id, changed_by, change_type, old_data_json, new_data_json,
                old_visibility_level, new_visibility_level, changed_at, comment
            )
            VALUES (%s, %s, 'updated', %s, %s, 'private', 'private', %s, %s);
            """,
            (
                hidden_entry_id,
                1000,
                Jsonb({"summary": "old hidden"}),
                Jsonb({"summary": "new hidden"}),
                hidden_changed_at,
                "Hidden update",
            ),
        )
        conn.commit()

    anonymous_resp = client.get("/history")
    assert anonymous_resp.status_code == 200
    assert anonymous_resp.json()["total"] == 0

    response = client.get("/history?limit=10&offset=0", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["limit"] == 10
    assert payload["offset"] == 0
    assert payload["total"] == 2
    assert [item["entry_id"] for item in payload["items"]] == [own_entry_id, granted_entry_id]
    assert payload["items"][0]["entry_title"] == "Own Visible Entry"
    assert payload["items"][0]["changed_fields"] == ["summary", "visibility_level"]
    assert payload["items"][1]["changed_by_username"] == "history_reader"
    assert payload["items"][1]["changed_fields"] == ["summary"]

    search_resp = client.get("/history?search=Granted", headers=auth_headers)
    assert search_resp.status_code == 200
    assert search_resp.json()["total"] == 1
    assert search_resp.json()["items"][0]["entry_id"] == granted_entry_id

    filter_resp = client.get(
        f"/history?schema_id={schema_id}&changed_by=1000&change_type=updated&limit=1&offset=0",
        headers=auth_headers,
    )
    assert filter_resp.status_code == 200
    filter_payload = filter_resp.json()
    assert filter_payload["total"] == 1
    assert len(filter_payload["items"]) == 1
    assert filter_payload["items"][0]["entry_id"] == granted_entry_id
