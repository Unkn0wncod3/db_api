
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

    get_resp = client.get(f"/persons/{person_id}")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()
    assert retrieved["first_name"] == "Ada"

    update_payload = {"city": "Berlin", "status": "inactive"}
    update_resp = client.patch(f"/persons/{person_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["city"] == "Berlin"
    assert updated["status"] == "inactive"

    delete_resp = client.delete(f"/persons/{person_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] == person_id

    missing_resp = client.get(f"/persons/{person_id}")
    assert missing_resp.status_code == 404
    assert missing_resp.json()["detail"] == "Person not found"
