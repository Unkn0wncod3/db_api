import uuid


def test_user_update_supports_mutable_fields_and_metadata(client):
    base_username = f"user-{uuid.uuid4().hex[:10]}"
    create_payload = {
        "username": base_username,
        "password": "InitialPass123!",
        "role": "user",
        "profile_picture_url": "https://example.com/avatar.png",
        "preferences": {"theme": "dark", "notifications": {"email": True}},
    }

    create_resp = client.post("/users", json=create_payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    user_id = created["id"]
    assert created["profile_picture_url"] == "https://example.com/avatar.png"
    assert created["preferences"]["theme"] == "dark"

    patch_payload = {
        "username": f"{base_username}_updated",
        "password": "NewPass456!",
        "profile_picture_url": None,
        "preferences": {"language": "de"},
    }
    patch_resp = client.patch(f"/users/{user_id}", json=patch_payload)
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["username"] == patch_payload["username"]
    assert updated["profile_picture_url"] is None
    assert updated["preferences"] == {"language": "de"}

    login_resp = client.post(
        "/auth/login",
        json={"username": patch_payload["username"], "password": patch_payload["password"]},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert login_data["user"]["username"] == patch_payload["username"]
    assert login_data["user"]["preferences"] == {"language": "de"}

    delete_resp = client.delete(f"/users/{user_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["id"] == user_id


def test_user_patch_requires_fields(client):
    username = f"user-{uuid.uuid4().hex[:8]}"
    create_resp = client.post(
        "/users",
        json={"username": username, "password": "AnotherPass123!", "role": "user"},
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    empty_patch = client.patch(f"/users/{user_id}", json={})
    assert empty_patch.status_code == 400
    assert empty_patch.json()["detail"] == "No fields to update"

    client.delete(f"/users/{user_id}")
