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


def test_dashboard_endpoint_returns_overview_totals_and_latest_entries(client):
    _ensure_test_actor()
    auth_headers = _auth_headers()

    person_schema = client.post(
        "/schemas",
        json={
            "key": "dashboard_person",
            "name": "Dashboard Person",
            "description": "Dashboard test schema",
            "icon": "user",
            "is_active": True,
        },
    )
    assert person_schema.status_code == 201
    person_schema_id = person_schema.json()["id"]

    vehicle_schema = client.post(
        "/schemas",
        json={
            "key": "dashboard_vehicle",
            "name": "Dashboard Vehicle",
            "description": "Dashboard test schema",
            "icon": "car",
            "is_active": True,
        },
    )
    assert vehicle_schema.status_code == 201
    vehicle_schema_id = vehicle_schema.json()["id"]

    created_ids = []
    creation_specs = [
        (person_schema_id, "Alpha", "draft"),
        (person_schema_id, "Beta", "active"),
        (vehicle_schema_id, "Car One", "active"),
        (vehicle_schema_id, "Car Two", "active"),
        (person_schema_id, "Gamma", "review"),
        (vehicle_schema_id, "Car Three", "active"),
    ]
    for schema_id, title, status in creation_specs:
        resp = client.post(
            "/entries",
            json={
                "schema_id": schema_id,
                "title": title,
                "status": status,
                "visibility_level": "internal",
                "data_json": {},
            },
        )
        assert resp.status_code == 201
        created_ids.append(resp.json()["id"])

    beta_id = created_ids[1]
    newest_created_id = created_ids[-1]

    update_resp = client.patch(
        f"/entries/{beta_id}",
        json={
            "status": "review",
            "comment": "Dashboard freshness test",
        },
    )
    assert update_resp.status_code == 200

    response = client.get("/dashboard", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["total_entries"] == 6
    assert len(payload["latest_created"]) == 5
    assert len(payload["latest_updated"]) == 5
    assert payload["latest_created"][0]["id"] == newest_created_id
    assert payload["latest_created"][0]["schema_key"] == "dashboard_vehicle"
    assert payload["latest_updated"][0]["id"] == beta_id
    assert payload["latest_updated"][0]["status"] == "review"

    totals = {row["schema_key"]: row for row in payload["totals_per_schema"]}
    assert totals["dashboard_person"]["total_entries"] == 3
    assert totals["dashboard_vehicle"]["total_entries"] == 3
