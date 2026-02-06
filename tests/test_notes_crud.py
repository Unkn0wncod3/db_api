
import uuid


def test_notes_full_crud_flow(client):
    person_payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": f"note-test-{uuid.uuid4()}@example.com",
        "tags": None,
        "metadata": None,
    }
    person_resp = client.post("/persons", json=person_payload)
    assert person_resp.status_code == 201
    person = person_resp.json()
    person_id = person["id"]

    note_payload = {
        "title": "Initial title",
        "text": "Initial text",
        "pinned": False,
    }
    create_resp = client.post(f"/notes/by-person/{person_id}", json=note_payload)
    assert create_resp.status_code == 201
    note = create_resp.json()
    note_id = note["id"]
    assert note["person_id"] == person_id
    assert note["title"] == note_payload["title"]
    assert note["visibility_level"] == "user"

    read_resp = client.get(f"/notes/{note_id}")
    assert read_resp.status_code == 200
    assert read_resp.json()["text"] == note_payload["text"]

    update_payload = {"title": "Updated title", "pinned": True}
    update_resp = client.patch(f"/notes/{note_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated_note = update_resp.json()
    assert updated_note["title"] == update_payload["title"]
    assert updated_note["pinned"] is True

    delete_resp = client.delete(f"/notes/{note_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] == note_id

    missing_resp = client.get(f"/notes/{note_id}")
    assert missing_resp.status_code == 404
    assert missing_resp.json()["detail"] == "Note not found"

    cleanup_resp = client.delete(f"/persons/{person_id}")
    assert cleanup_resp.status_code == 200
    assert cleanup_resp.json()["deleted"] == person_id
