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


def test_relation_update_and_delete_endpoints(client):
    _ensure_test_actor()
    auth_headers = _auth_headers()
    schema_resp = client.post(
        "/schemas",
        json={
            "key": "relation_crud_case",
            "name": "Relation CRUD Case",
            "description": "Schema for relation CRUD test",
            "icon": "git-branch",
            "is_active": True,
        },
    )
    assert schema_resp.status_code == 201
    schema_id = schema_resp.json()["id"]

    from_entry_resp = client.post(
        "/entries",
        json={
            "schema_id": schema_id,
            "title": "From Entry",
            "status": "open",
            "visibility_level": "internal",
            "data_json": {},
        },
    )
    assert from_entry_resp.status_code == 201
    from_entry_id = from_entry_resp.json()["id"]

    to_entry_resp = client.post(
        "/entries",
        json={
            "schema_id": schema_id,
            "title": "To Entry",
            "status": "open",
            "visibility_level": "internal",
            "data_json": {},
        },
    )
    assert to_entry_resp.status_code == 201
    to_entry_id = to_entry_resp.json()["id"]

    second_target_resp = client.post(
        "/entries",
        json={
            "schema_id": schema_id,
            "title": "Second Target",
            "status": "open",
            "visibility_level": "internal",
            "data_json": {},
        },
    )
    assert second_target_resp.status_code == 201
    second_target_id = second_target_resp.json()["id"]

    create_relation_resp = client.post(
        f"/entries/{from_entry_id}/relations",
        json={
            "to_entry_id": to_entry_id,
            "relation_type": "related_to",
            "sort_order": 1,
            "metadata_json": {"origin": "initial"},
        },
    )
    assert create_relation_resp.status_code == 201
    relation = create_relation_resp.json()
    relation_id = relation["id"]

    patch_resp = client.patch(
        f"/entries/{from_entry_id}/relations/{relation_id}",
        json={
            "to_entry_id": second_target_id,
            "relation_type": "references",
            "sort_order": 5,
            "metadata_json": {"origin": "updated"},
        },
    )
    assert patch_resp.status_code == 200
    patched = patch_resp.json()
    assert patched["id"] == relation_id
    assert patched["to_entry_id"] == second_target_id
    assert patched["relation_type"] == "references"
    assert patched["sort_order"] == 5
    assert patched["metadata_json"]["origin"] == "updated"

    list_resp = client.get(f"/entries/{from_entry_id}/relations", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["id"] == relation_id

    delete_resp = client.delete(f"/entries/{from_entry_id}/relations/{relation_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["id"] == relation_id

    final_list_resp = client.get(f"/entries/{from_entry_id}/relations", headers=auth_headers)
    assert final_list_resp.status_code == 200
    assert final_list_resp.json() == []
