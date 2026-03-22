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


def test_entry_lookup_returns_minimal_visible_entries_with_search_and_limit(client):
    _ensure_test_actor()
    auth_headers = _auth_headers()

    schema_resp = client.post(
        "/schemas",
        json={
            "key": "entry_lookup_case",
            "name": "Entry Lookup Case",
            "description": "Schema for entry lookup endpoint test",
            "icon": "search",
            "is_active": True,
        },
    )
    assert schema_resp.status_code == 201
    schema = schema_resp.json()
    schema_id = schema["id"]

    for title in ("Alpha Contact", "Alpha Vehicle", "Beta Case"):
        create_resp = client.post(
            "/entries",
            json={
                "schema_id": schema_id,
                "title": title,
                "status": "open",
                "visibility_level": "internal",
                "data_json": {},
            },
        )
        assert create_resp.status_code == 201

    response = client.get("/entries/lookup?q=Alpha&limit=1", headers=auth_headers)
    assert response.status_code == 200

    payload = response.json()
    assert len(payload) == 1
    assert payload[0] == {
        "id": payload[0]["id"],
        "title": "Alpha Vehicle",
        "schema_id": schema_id,
        "schema_key": "entry_lookup_case",
        "schema_name": "Entry Lookup Case",
    }

    filtered_response = client.get(f"/entries/lookup?schema_id={schema_id}", headers=auth_headers)
    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()
    assert len(filtered_payload) == 3
    assert all(set(item.keys()) == {"id", "title", "schema_id", "schema_key", "schema_name"} for item in filtered_payload)
