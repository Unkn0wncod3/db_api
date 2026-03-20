from api.app.db import get_connection


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


def test_schema_update_and_delete_endpoints(client):
    _ensure_test_actor()
    create_resp = client.post(
        "/schemas",
        json={
            "key": "schema_crud_case",
            "name": "Schema CRUD Case",
            "description": "Schema for schema CRUD test",
            "icon": "layers",
            "is_active": True,
        },
    )
    assert create_resp.status_code == 201
    schema_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/schemas/{schema_id}",
        json={
            "name": "Schema CRUD Case Updated",
            "description": "Updated description",
            "is_active": False,
        },
    )
    assert patch_resp.status_code == 200
    patched = patch_resp.json()
    assert patched["id"] == schema_id
    assert patched["name"] == "Schema CRUD Case Updated"
    assert patched["description"] == "Updated description"
    assert patched["is_active"] is False

    delete_resp = client.delete(f"/schemas/{schema_id}")
    assert delete_resp.status_code == 200
    deleted = delete_resp.json()
    assert deleted["id"] == schema_id
    assert deleted["name"] == "Schema CRUD Case Updated"


def test_schema_delete_cascades_entries(client):
    _ensure_test_actor()
    create_resp = client.post(
        "/schemas",
        json={
            "key": "schema_delete_cascade",
            "name": "Schema Delete Cascade",
            "description": "Schema for delete cascade test",
            "icon": "triangle-alert",
            "is_active": True,
        },
    )
    assert create_resp.status_code == 201
    schema_id = create_resp.json()["id"]

    entry_resp = client.post(
        "/entries",
        json={
            "schema_id": schema_id,
            "title": "Blocking Entry",
            "status": "open",
            "visibility_level": "internal",
            "data_json": {},
        },
    )
    assert entry_resp.status_code == 201
    entry_id = entry_resp.json()["id"]

    delete_resp = client.delete(f"/schemas/{schema_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["id"] == schema_id

    get_schema_resp = client.get(f"/schemas/{schema_id}")
    assert get_schema_resp.status_code == 404

    get_entry_resp = client.get(f"/entries/{entry_id}")
    assert get_entry_resp.status_code == 404
