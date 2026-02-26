import uuid


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
