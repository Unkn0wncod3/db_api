
import uuid


def test_profiles_full_crud_flow(client):
    platform_payload = {
        "name": f"profile-platform-{uuid.uuid4()}",
        "category": "social",
        "base_url": "https://profiles.example.com",
        "api_base_url": "https://api.profiles.example.com",
        "is_active": True,
    }
    platform_resp = client.post("/platforms", json=platform_payload)
    assert platform_resp.status_code == 201
    platform = platform_resp.json()
    platform_id = platform["id"]

    profile_payload = {
        "platform_id": platform_id,
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "display_name": "Initial User",
        "status": "active",
        "metadata": None,
        "visibility_level": "admin",
    }
    create_resp = client.post("/profiles", json=profile_payload)
    assert create_resp.status_code == 201
    profile = create_resp.json()
    profile_id = profile["id"]
    assert profile["username"] == profile_payload["username"]
    assert profile["visibility_level"] == "admin"

    list_resp = client.get("/profiles", params={"username": profile_payload["username"]})
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert any(item["id"] == profile_id for item in items)

    update_payload = {"display_name": "Updated User", "is_verified": True}
    update_resp = client.patch(f"/profiles/{profile_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["display_name"] == "Updated User"
    assert updated["is_verified"] is True
    assert updated["visibility_level"] == "admin"

    delete_resp = client.delete(f"/profiles/{profile_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] == profile_id

    missing_resp = client.patch(f"/profiles/{profile_id}", json={"display_name": "again"})
    assert missing_resp.status_code == 404

    cleanup_platform = client.delete(f"/platforms/{platform_id}")
    assert cleanup_platform.status_code == 200
    assert cleanup_platform.json()["deleted"] == platform_id
