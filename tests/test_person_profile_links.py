
import uuid


def test_person_profile_linking_flow(client):
    person_payload = {
        "first_name": "Link",
        "last_name": "Tester",
        "email": f"link-test-{uuid.uuid4()}@example.com",
        "tags": None,
        "metadata": None,
    }
    person_resp = client.post("/persons", json=person_payload)
    assert person_resp.status_code == 201
    person = person_resp.json()
    person_id = person["id"]

    platform_payload = {
        "name": f"link-platform-{uuid.uuid4()}",
        "category": "social",
        "base_url": "https://links.example.com",
        "api_base_url": "https://api.links.example.com",
        "is_active": True,
    }
    platform_resp = client.post("/platforms", json=platform_payload)
    assert platform_resp.status_code == 201
    platform_id = platform_resp.json()["id"]

    profile_payload = {
        "platform_id": platform_id,
        "username": f"link_user_{uuid.uuid4().hex[:8]}",
        "display_name": "Link User",
        "status": "active",
        "metadata": None,
    }
    profile_resp = client.post("/profiles", json=profile_payload)
    assert profile_resp.status_code == 201
    profile_id = profile_resp.json()["id"]

    link_payload = {"profile_id": profile_id, "note": "Initial link"}
    link_resp = client.post(f"/persons/{person_id}/profiles", json=link_payload)
    assert link_resp.status_code == 201
    link_data = link_resp.json()
    assert link_data["person_id"] == person_id
    assert link_data["profile_id"] == profile_id
    assert link_data["note"] == "Initial link"

    list_resp = client.get(f"/persons/{person_id}/profiles")
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert any(item["profile_id"] == profile_id for item in items)

    relink_payload = {"profile_id": profile_id, "note": "Updated note"}
    relink_resp = client.post(f"/persons/{person_id}/profiles", json=relink_payload)
    assert relink_resp.status_code == 201
    relink_data = relink_resp.json()
    assert relink_data["note"] == "Updated note"

    delete_resp = client.delete(f"/persons/{person_id}/profiles/{profile_id}")
    assert delete_resp.status_code == 200
    deleted = delete_resp.json()["deleted"]
    assert deleted["person_id"] == person_id
    assert deleted["profile_id"] == profile_id

    empty_resp = client.get(f"/persons/{person_id}/profiles")
    assert empty_resp.status_code == 200
    assert empty_resp.json()["items"] == []

    profile_delete = client.delete(f"/profiles/{profile_id}")
    assert profile_delete.status_code == 200
    assert profile_delete.json()["deleted"] == profile_id

    platform_delete = client.delete(f"/platforms/{platform_id}")
    assert platform_delete.status_code == 200
    assert platform_delete.json()["deleted"] == platform_id

    person_delete = client.delete(f"/persons/{person_id}")
    assert person_delete.status_code == 200
    assert person_delete.json()["deleted"] == person_id
