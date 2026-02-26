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
    pre = client.get("/audit/logs", params={"limit": 5})
    assert pre.status_code == 200

    delete_resp = client.delete("/audit/logs")
    assert delete_resp.status_code == 204

    post = client.get("/audit/logs", params={"limit": 5})
    assert post.status_code == 200
    assert post.json()["items"] == []
