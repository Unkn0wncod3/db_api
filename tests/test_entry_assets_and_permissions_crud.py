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


def _create_entry_for_crud_tests(client, schema_key: str, schema_name: str) -> int:
    schema_resp = client.post(
        "/schemas",
        json={
            "key": schema_key,
            "name": schema_name,
            "description": "Schema for attachment and permission CRUD tests",
            "icon": "paperclip",
            "is_active": True,
        },
    )
    assert schema_resp.status_code == 201
    schema_id = schema_resp.json()["id"]

    entry_resp = client.post(
        "/entries",
        json={
            "schema_id": schema_id,
            "title": "CRUD Entry",
            "status": "open",
            "visibility_level": "internal",
            "data_json": {},
        },
    )
    assert entry_resp.status_code == 201
    return entry_resp.json()["id"]


def test_attachment_update_and_delete_endpoints(client):
    _ensure_test_actor()
    auth_headers = _auth_headers()
    entry_id = _create_entry_for_crud_tests(client, "entry_attachments_crud_case", "Entry Attachments CRUD Case")

    create_resp = client.post(
        f"/entries/{entry_id}/attachments",
        json={
            "file_name": "briefing.pdf",
            "external_url": "https://example.com/briefing.pdf",
            "mime_type": "application/pdf",
            "file_size": 123,
            "checksum": "briefing-v1",
            "description": "Initial attachment",
        },
    )
    assert create_resp.status_code == 201
    attachment_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/entries/{entry_id}/attachments/{attachment_id}",
        json={
            "file_name": "briefing-v2.pdf",
            "external_url": "https://example.com/briefing-v2.pdf",
            "mime_type": "application/pdf",
            "file_size": 456,
            "checksum": "briefing-v2",
            "description": "Updated attachment",
        },
    )
    assert patch_resp.status_code == 200
    patched = patch_resp.json()
    assert patched["id"] == attachment_id
    assert patched["file_name"] == "briefing-v2.pdf"
    assert patched["stored_path"] == "https://example.com/briefing-v2.pdf"
    assert patched["file_size"] == 456
    assert patched["checksum"] == "briefing-v2"
    assert patched["description"] == "Updated attachment"

    list_resp = client.get(f"/entries/{entry_id}/attachments", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["id"] == attachment_id

    delete_resp = client.delete(f"/entries/{entry_id}/attachments/{attachment_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["id"] == attachment_id

    final_list_resp = client.get(f"/entries/{entry_id}/attachments", headers=auth_headers)
    assert final_list_resp.status_code == 200
    assert final_list_resp.json() == []


def test_permission_update_and_delete_endpoints(client):
    _ensure_test_actor()
    auth_headers = _auth_headers()
    entry_id = _create_entry_for_crud_tests(client, "entry_permissions_crud_case", "Entry Permissions CRUD Case")

    create_resp = client.post(
        f"/entries/{entry_id}/permissions",
        json={
            "subject_type": "role",
            "subject_id": "reader",
            "permission": "read",
        },
    )
    assert create_resp.status_code == 201
    permission_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/entries/{entry_id}/permissions/{permission_id}",
        json={
            "subject_type": "role",
            "subject_id": "editor",
            "permission": "edit",
        },
    )
    assert patch_resp.status_code == 200
    patched = patch_resp.json()
    assert patched["id"] == permission_id
    assert patched["subject_type"] == "role"
    assert patched["subject_id"] == "editor"
    assert patched["permission"] == "edit"

    list_resp = client.get(f"/entries/{entry_id}/permissions", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["id"] == permission_id

    delete_resp = client.delete(f"/entries/{entry_id}/permissions/{permission_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["id"] == permission_id

    final_list_resp = client.get(f"/entries/{entry_id}/permissions", headers=auth_headers)
    assert final_list_resp.status_code == 200
    assert final_list_resp.json() == []
