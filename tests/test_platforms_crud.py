

def test_platforms_full_crud_flow(client):
    create_payload = {
        "name": "My Platform",
        "category": "social",
        "base_url": "https://example.com",
        "api_base_url": "https://api.example.com",
        "is_active": True,
        "visibility_level": "admin",
    }
    create_resp = client.post("/platforms", json=create_payload)
    assert create_resp.status_code == 201
    platform = create_resp.json()
    platform_id = platform["id"]
    assert platform["name"] == create_payload["name"]
    assert platform["visibility_level"] == "admin"

    get_resp = client.get("/platforms")
    assert get_resp.status_code == 200
    ids = [item["id"] for item in get_resp.json()["items"]]
    assert platform_id in ids

    update_payload = {"name": "Updated Platform", "is_active": False}
    update_resp = client.patch(f"/platforms/{platform_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["name"] == "Updated Platform"
    assert updated["is_active"] is False
    assert updated["visibility_level"] == "admin"

    delete_resp = client.delete(f"/platforms/{platform_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] == platform_id

    missing_resp = client.patch(f"/platforms/{platform_id}", json={"name": "again"})
    assert missing_resp.status_code == 404
