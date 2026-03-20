from api.app.db import get_connection
from api.app.security import create_access_token


def _ensure_test_actor() -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (id, username, password_hash, role, is_active, preferences)
            VALUES (999, 'test_head_admin', 'test-hash', 'head_admin', TRUE, '{}'::jsonb)
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
    token = create_access_token({"id": 999, "role": "head_admin"})
    return {"Authorization": f"Bearer {token}"}


def test_schema_entries_endpoint_returns_schema_fields_entries_and_access(client):
    _ensure_test_actor()
    auth_headers = _auth_headers()

    schema_resp = client.post(
        "/schemas",
        json={
            "key": "schema_entries_case",
            "name": "Schema Entries Case",
            "description": "Schema for schema entries endpoint test",
            "icon": "layers",
            "is_active": True,
        },
    )
    assert schema_resp.status_code == 201
    schema_id = schema_resp.json()["id"]

    field_resp = client.post(
        f"/schemas/{schema_id}/fields",
        json={
            "key": "summary",
            "label": "Summary",
            "description": "Short summary",
            "data_type": "text",
            "is_required": True,
            "is_unique": False,
            "default_value": None,
            "sort_order": 10,
            "is_active": True,
            "validation_json": {"min_length": 3},
            "settings_json": {},
        },
    )
    assert field_resp.status_code == 201

    primary_resp = client.post(
        "/entries",
        json={
            "schema_id": schema_id,
            "title": "Primary Entry",
            "status": "open",
            "visibility_level": "internal",
            "data_json": {"summary": "First summary"},
        },
    )
    assert primary_resp.status_code == 201
    primary_id = primary_resp.json()["id"]

    secondary_resp = client.post(
        "/entries",
        json={
            "schema_id": schema_id,
            "title": "Secondary Entry",
            "status": "draft",
            "visibility_level": "private",
            "data_json": {"summary": "Second summary"},
        },
    )
    assert secondary_resp.status_code == 201

    response = client.get(f"/schemas/{schema_id}/entries", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["schema"]["id"] == schema_id
    assert len(payload["schema"]["fields"]) == 1
    assert payload["schema"]["fields"][0]["key"] == "summary"
    assert len(payload["entries"]) == 2

    primary_entry = next(item for item in payload["entries"] if item["id"] == primary_id)
    assert primary_entry["data_json"]["summary"] == "First summary"
    assert primary_entry["access"]["read"] is True
    assert primary_entry["access"]["edit"] is True
    assert primary_entry["access"]["manage_permissions"] is True
