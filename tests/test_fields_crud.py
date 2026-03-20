def test_fields_crud_endpoints(client):
    schema_resp = client.post(
        "/schemas",
        json={
            "key": "field_crud_case",
            "name": "Field CRUD Case",
            "description": "Schema for field CRUD test",
            "icon": "list",
            "is_active": True,
        },
    )
    assert schema_resp.status_code == 201
    schema_id = schema_resp.json()["id"]

    create_resp = client.post(
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
    assert create_resp.status_code == 201
    field = create_resp.json()
    field_id = field["id"]

    list_resp = client.get(f"/schemas/{schema_id}/fields")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["id"] == field_id

    get_resp = client.get(f"/schemas/{schema_id}/fields/{field_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["key"] == "summary"

    patch_resp = client.patch(
        f"/schemas/{schema_id}/fields/{field_id}",
        json={
            "label": "Summary Updated",
            "sort_order": 20,
            "validation_json": {"min_length": 5},
        },
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["label"] == "Summary Updated"
    assert patch_resp.json()["sort_order"] == 20
    assert patch_resp.json()["validation_json"]["min_length"] == 5

    delete_resp = client.delete(f"/schemas/{schema_id}/fields/{field_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["id"] == field_id

    final_list_resp = client.get(f"/schemas/{schema_id}/fields")
    assert final_list_resp.status_code == 200
    assert final_list_resp.json() == []
