
import uuid


def test_persons_full_crud_flow(client):
    unique_email = f"person-test-{uuid.uuid4()}@example.com"
    create_payload = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": unique_email,
        "tags": None,
        "metadata": None,
    }
    create_resp = client.post("/persons", json=create_payload)
    assert create_resp.status_code == 201
    person = create_resp.json()
    person_id = person["id"]
    assert person["email"] == unique_email
    assert person["visibility_level"] == "user"

    get_resp = client.get(f"/persons/{person_id}")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()
    assert retrieved["first_name"] == "Ada"
    assert retrieved["visibility_level"] == "user"

    update_payload = {"city": "Berlin", "status": "inactive"}
    update_resp = client.patch(f"/persons/{person_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["city"] == "Berlin"
    assert updated["status"] == "inactive"
    assert updated["visibility_level"] == "user"

    delete_resp = client.delete(f"/persons/{person_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] == person_id

    missing_resp = client.get(f"/persons/{person_id}")
    assert missing_resp.status_code == 404
    assert missing_resp.json()["detail"] == "Person not found"


def test_person_visibility_filters_for_regular_users(client):
    admin_headers = {"X-Test-Role": "admin"}
    user_headers = {"X-Test-Role": "user"}
    hidden_email = f"admin-only-{uuid.uuid4()}@example.com"
    create_payload = {
        "first_name": "Hidden",
        "last_name": "Person",
        "email": hidden_email,
        "visibility_level": "admin",
        "tags": None,
        "metadata": None,
    }
    create_resp = client.post("/persons", json=create_payload, headers=admin_headers)
    assert create_resp.status_code == 201
    person = create_resp.json()
    person_id = person["id"]
    assert person["visibility_level"] == "admin"

    user_get = client.get(f"/persons/{person_id}", headers=user_headers)
    assert user_get.status_code == 404

    user_list = client.get("/persons", headers=user_headers).json()["items"]
    assert all(entry["visibility_level"] == "user" for entry in user_list)
    assert all(entry["email"] != hidden_email for entry in user_list)

    cleanup = client.delete(f"/persons/{person_id}", headers=admin_headers)
    assert cleanup.status_code == 200
