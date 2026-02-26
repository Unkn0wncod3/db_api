import uuid


def _audit_entries(client, limit=100):
    resp = client.get("/audit/logs", params={"limit": limit})
    assert resp.status_code == 200
    return [
        entry
        for entry in resp.json()["items"]
        if entry.get("metadata", {}).get("event") != "audit_logs_cleared"
    ]


def test_audit_log_records_user_lifecycle_actions(client):
    username = f"audit-user-{uuid.uuid4().hex[:8]}"
    create_resp = client.post(
        "/users",
        json={"username": username, "password": "AuditPass!234", "role": "user"},
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    patch_resp = client.patch(f"/users/{user_id}", json={"is_active": False})
    assert patch_resp.status_code == 200

    logs_resp = client.get(
        "/audit/logs",
        params={"limit": 50, "resource": "/users/{user_id}"},
    )
    assert logs_resp.status_code == 200
    entries = logs_resp.json()["items"]
    assert any(
        entry["resource_id"] == user_id and entry["action"].startswith("PATCH /users")
        for entry in entries
    )

    delete_resp = client.delete(f"/users/{user_id}")
    assert delete_resp.status_code == 200


def test_audit_log_filter_by_user_id(client):
    baseline = client.get("/users")
    assert baseline.status_code == 200

    resp = client.get("/audit/logs", params={"limit": 10, "user_id": 999})
    assert resp.status_code == 200
    payload = resp.json()
    assert "items" in payload
    assert payload["limit"] == 10
    assert payload["items"], "expected audit log entries for user_id 999"
    assert all(entry["user_id"] == 999 for entry in payload["items"])


def test_login_attempts_are_logged_with_username(client):
    username = f"login-audit-{uuid.uuid4().hex[:8]}"
    create_resp = client.post(
        "/users",
        json={"username": username, "password": "SecurePass!789", "role": "user"},
    )
    assert create_resp.status_code == 201

    bad_login = client.post("/auth/login", json={"username": username, "password": "wrong"})
    assert bad_login.status_code == 401

    logs_resp = client.get("/audit/logs", params={"limit": 20, "action": "POST /auth/login"})
    assert logs_resp.status_code == 200
    entries = logs_resp.json()["items"]
    assert any(
        entry["path"] == "/auth/login"
        and entry["metadata"].get("username") == username
        and entry["metadata"].get("outcome") in {"invalid_password", "invalid_username_or_inactive"}
        for entry in entries
    )

    client.delete(f"/users/{create_resp.json()['id']}")


def test_token_is_logged_even_for_unknown_route(client):
    username = f"audit-missing-{uuid.uuid4().hex[:8]}"
    password = "MissingRoute123!"
    create_resp = client.post(
        "/users",
        json={"username": username, "password": password, "role": "user"},
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    login_resp = client.post("/auth/login", json={"username": username, "password": password})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    missing = client.get(
        "/no-such-endpoint",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Forwarded-For": "203.0.113.5, 10.0.0.1",
        },
    )
    assert missing.status_code == 404

    logs = client.get("/audit/logs", params={"limit": 20})
    assert logs.status_code == 200
    entries = logs.json()["items"]
    assert any(
        entry["path"] == "/no-such-endpoint"
        and entry["user_id"] == user_id
        and entry["ip_address"] == "203.0.113.5"
        for entry in entries
    )

    client.delete(f"/users/{user_id}")


def test_admin_can_delete_audit_logs(client):
    client.delete("/audit/logs")
    delete_resp = client.delete("/audit/logs")
    assert delete_resp.status_code == 204

    post = client.get("/audit/logs", params={"limit": 5})
    assert post.status_code == 200
    items = post.json()["items"]
    assert items
    assert items[0]["metadata"].get("event") == "audit_logs_cleared"


def test_noise_requests_are_ignored(client):
    client.delete("/audit/logs")

    root_resp = client.get("/")
    assert root_resp.status_code == 200

    options_resp = client.options("/users")
    assert options_resp.status_code in {200, 204}

    assert _audit_entries(client, limit=5) == []


def test_user_crud_events_emit_metadata(client):
    client.delete("/audit/logs")
    username = f"audit-user-{uuid.uuid4().hex[:6]}"
    create_resp = client.post(
        "/users",
        json={"username": username, "password": "MetaPass!123", "role": "user"},
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/users/{user_id}",
        json={"profile_picture_url": "https://example.com/avatar.png"},
    )
    assert patch_resp.status_code == 200

    delete_resp = client.delete(f"/users/{user_id}")
    assert delete_resp.status_code == 200

    entries = _audit_entries(client, limit=10)
    events = [entry["metadata"].get("event") for entry in entries]
    assert "user_created" in events
    assert "user_updated" in events
    assert "user_deleted" in events


def test_person_profile_note_activity_metadata(client):
    client.delete("/audit/logs")
    person_payload = {
        "first_name": "Audit",
        "last_name": uuid.uuid4().hex[:8],
        "email": "audit@example.com",
    }
    person_resp = client.post("/persons", json=person_payload)
    assert person_resp.status_code == 201
    person_id = person_resp.json()["id"]

    update_person = client.patch(f"/persons/{person_id}", json={"city": "Berlin"})
    assert update_person.status_code == 200

    platform_name = f"platform-{uuid.uuid4().hex[:6]}"
    platform_resp = client.post(
        "/platforms",
        json={"name": platform_name, "category": "social", "is_active": True},
    )
    assert platform_resp.status_code == 201
    platform_id = platform_resp.json()["id"]

    profile_resp = client.post(
        "/profiles",
        json={"platform_id": platform_id, "username": f"user_{uuid.uuid4().hex[:6]}"},
    )
    assert profile_resp.status_code == 201
    profile_id = profile_resp.json()["id"]

    update_profile = client.patch(
        f"/profiles/{profile_id}",
        json={"display_name": "New Display"},
    )
    assert update_profile.status_code == 200

    link_resp = client.post(
        f"/persons/{person_id}/profiles",
        json={"profile_id": profile_id, "note": "primary"},
    )
    assert link_resp.status_code == 201

    unlink_resp = client.delete(f"/persons/{person_id}/profiles/{profile_id}")
    assert unlink_resp.status_code == 200

    delete_profile = client.delete(f"/profiles/{profile_id}")
    assert delete_profile.status_code == 200

    note_resp = client.post(
        f"/notes/by-person/{person_id}",
        json={"title": "Audit Note", "text": "text", "pinned": False},
    )
    assert note_resp.status_code == 201
    note_id = note_resp.json()["id"]

    update_note = client.patch(f"/notes/{note_id}", json={"pinned": True})
    assert update_note.status_code == 200

    delete_note = client.delete(f"/notes/{note_id}")
    assert delete_note.status_code == 200

    activity_resp = client.post(
        "/activities",
        json={
            "person_id": person_id,
            "activity_type": "login",
            "item": "web",
            "notes": "audit",
        },
    )
    assert activity_resp.status_code == 201
    activity_id = activity_resp.json()["id"]

    update_activity = client.patch(f"/activities/{activity_id}", json={"severity": "info"})
    assert update_activity.status_code == 200

    delete_activity = client.delete(f"/activities/{activity_id}")
    assert delete_activity.status_code == 200

    delete_person = client.delete(f"/persons/{person_id}")
    assert delete_person.status_code == 200

    entries = _audit_entries(client, limit=100)
    events = [entry["metadata"].get("event") for entry in entries if entry.get("metadata")]
    expected_events = {
        "person_created",
        "person_updated",
        "profile_created",
        "profile_updated",
        "profile_linked",
        "profile_unlinked",
        "profile_deleted",
        "note_created",
        "note_updated",
        "note_deleted",
        "activity_created",
        "activity_updated",
        "activity_deleted",
        "person_deleted",
    }
    for event in expected_events:
        assert event in events
