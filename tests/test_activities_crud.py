
import uuid


def test_activities_full_crud_flow(client):
    person_payload = {
        "first_name": "Grace",
        "last_name": "Hopper",
        "email": f"activity-test-{uuid.uuid4()}@example.com",
        "tags": None,
        "metadata": None,
    }
    person_resp = client.post("/persons", json=person_payload)
    assert person_resp.status_code == 201
    person = person_resp.json()
    person_id = person["id"]

    activity_payload = {
        "person_id": person_id,
        "activity_type": "login",
        "occurred_at": "2024-01-01T00:00:00Z",
        "item": "initial-item",
        "notes": "Initial notes",
        "details": None,
        "visibility_level": "user",
    }
    create_resp = client.post("/activities", json=activity_payload)
    assert create_resp.status_code == 201
    activity = create_resp.json()
    activity_id = activity["id"]
    assert activity["person_id"] == person_id
    assert activity["item"] == "initial-item"
    assert activity["visibility_level"] == "user"

    list_resp = client.get("/activities", params={"person_id": person_id})
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert any(entry["id"] == activity_id for entry in items)

    update_payload = {"notes": "Updated notes", "severity": "high"}
    update_resp = client.patch(f"/activities/{activity_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["notes"] == "Updated notes"
    assert updated["severity"] == "high"

    delete_resp = client.delete(f"/activities/{activity_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] == activity_id

    missing_resp = client.patch(f"/activities/{activity_id}", json={"notes": "again"})
    assert missing_resp.status_code == 404

    cleanup_resp = client.delete(f"/persons/{person_id}")
    assert cleanup_resp.status_code == 200
    assert cleanup_resp.json()["deleted"] == person_id
