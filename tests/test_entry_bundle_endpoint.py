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


def test_entry_bundle_endpoint_returns_detail_payload_in_one_response(client):
    _ensure_test_actor()
    auth_headers = _auth_headers()

    schema_resp = client.post(
        "/schemas",
        json={
            "key": "entry_bundle_case",
            "name": "Entry Bundle Case",
            "description": "Schema for entry bundle test",
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

    related_resp = client.post(
        "/entries",
        json={
            "schema_id": schema_id,
            "title": "Related Entry",
            "status": "draft",
            "visibility_level": "internal",
            "data_json": {"summary": "Second summary"},
        },
    )
    assert related_resp.status_code == 201
    related_id = related_resp.json()["id"]

    relation_resp = client.post(
        f"/entries/{primary_id}/relations",
        json={
            "to_entry_id": related_id,
            "relation_type": "related_to",
            "sort_order": 5,
            "metadata_json": {"origin": "test"},
        },
    )
    assert relation_resp.status_code == 201

    attachment_resp = client.post(
        f"/entries/{primary_id}/attachments",
        json={
            "file_name": "briefing.pdf",
            "external_url": "https://example.com/briefing.pdf",
            "mime_type": "application/pdf",
            "file_size": 123,
            "checksum": "entry-bundle-test-attachment",
            "description": "Test attachment",
        },
    )
    assert attachment_resp.status_code == 201

    permission_resp = client.post(
        f"/entries/{primary_id}/permissions",
        json={
            "subject_type": "role",
            "subject_id": "reader",
            "permission": "read",
        },
    )
    assert permission_resp.status_code == 201

    response = client.get(f"/entries/{primary_id}/bundle", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["entry"]["id"] == primary_id
    assert payload["schema"]["id"] == schema_id
    assert payload["schema"]["fields"][0]["key"] == "summary"
    assert payload["access"]["read"] is True
    assert payload["access"]["manage_permissions"] is True
    assert len(payload["history"]) >= 1
    assert len(payload["relations"]) == 1
    assert payload["relations"][0]["to_entry_id"] == related_id
    assert len(payload["attachments"]) == 1
    assert payload["attachments"][0]["file_name"] == "briefing.pdf"
    assert len(payload["permissions"]) == 1
    assert payload["permissions"][0]["permission"] == "read"
