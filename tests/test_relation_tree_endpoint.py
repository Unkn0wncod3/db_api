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


def _create_entry(client, schema_id: int, title: str) -> int:
    response = client.post(
        "/entries",
        json={
            "schema_id": schema_id,
            "title": title,
            "status": "open",
            "visibility_level": "internal",
            "data_json": {},
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_schema(client, key: str, name: str) -> int:
    response = client.post(
        "/schemas",
        json={
            "key": key,
            "name": name,
            "description": f"Schema for {name}",
            "icon": "git-branch",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_relation(client, from_entry_id: int, to_entry_id: int, sort_order: int) -> None:
    response = client.post(
        f"/entries/{from_entry_id}/relations",
        json={
            "to_entry_id": to_entry_id,
            "relation_type": "related_to",
            "sort_order": sort_order,
            "metadata_json": {},
        },
    )
    assert response.status_code == 201


def test_relation_tree_endpoint_handles_cycles_without_duplicate_expansion(client):
    _ensure_test_actor()
    auth_headers = _auth_headers()

    schema_id = _create_schema(client, "relation_tree_case", "Relation Tree Case")
    related_schema_id = _create_schema(client, "relation_tree_related", "Relation Tree Related")

    root_id = _create_entry(client, schema_id, "Root")
    x_id = _create_entry(client, schema_id, "X")
    y_id = _create_entry(client, schema_id, "Y")
    f_id = _create_entry(client, schema_id, "F")
    g_id = _create_entry(client, related_schema_id, "G")

    _create_relation(client, root_id, x_id, 1)
    _create_relation(client, x_id, y_id, 1)
    _create_relation(client, y_id, f_id, 1)
    _create_relation(client, y_id, g_id, 2)
    _create_relation(client, g_id, x_id, 3)

    response = client.get(f"/entries/{root_id}/relation-tree", headers=auth_headers)
    assert response.status_code == 200

    payload = response.json()
    assert payload["root_entry_id"] == root_id
    assert payload["tree"]["entry"]["id"] == root_id
    assert payload["tree"]["entry"]["schema_id"] == schema_id
    assert payload["tree"]["entry"]["schema"]["id"] == schema_id
    assert payload["tree"]["entry"]["schema"]["name"] == "Relation Tree Case"

    root_children = payload["tree"]["children"]
    assert [child["entry"]["id"] for child in root_children] == [x_id]

    x_node = root_children[0]
    assert x_node["is_reference"] is False
    assert x_node["via_relation"]["from_entry_id"] == root_id
    assert x_node["via_relation"]["to_entry_id"] == x_id
    assert x_node["via_relation"]["direction"] == "outgoing"

    y_children = x_node["children"]
    assert [child["entry"]["id"] for child in y_children] == [y_id, g_id]

    y_node = y_children[0]
    g_reference = y_children[1]
    assert y_node["is_reference"] is False
    assert g_reference["is_reference"] is True
    assert g_reference["reference_reason"] == "duplicate"

    nested_y_children = y_node["children"]
    assert [child["entry"]["id"] for child in nested_y_children] == [f_id, g_id]

    f_node = nested_y_children[0]
    g_node = nested_y_children[1]
    assert f_node["is_reference"] is False
    assert g_node["is_reference"] is False
    assert g_node["entry"]["schema_id"] == related_schema_id
    assert g_node["entry"]["schema"]["id"] == related_schema_id
    assert g_node["entry"]["schema"]["key"] == "relation_tree_related"
    assert g_node["entry"]["schema"]["name"] == "Relation Tree Related"

    cycle_children = g_node["children"]
    assert [child["entry"]["id"] for child in cycle_children] == [x_id]
    assert cycle_children[0]["is_reference"] is True
    assert cycle_children[0]["reference_reason"] == "cycle"
