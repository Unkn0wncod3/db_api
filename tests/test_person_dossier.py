import uuid

from api.app.services import dossiers as dossier_service


def _create_person_bundle(client, *, visibility_level="user"):
    admin_headers = {"X-Test-Role": "head_admin"}
    person_payload = {
        "first_name": "Dossier",
        "last_name": "Tester",
        "email": f"dossier-{uuid.uuid4()}@example.com",
        "visibility_level": visibility_level,
        "tags": None,
        "metadata": None,
    }
    person = client.post("/persons", json=person_payload, headers=admin_headers).json()
    person_id = person["id"]

    platform_payload = {
        "name": f"dossier-platform-{uuid.uuid4()}",
        "category": "social",
        "base_url": "https://example.com",
        "api_base_url": "https://api.example.com",
        "is_active": True,
    }
    platform = client.post("/platforms", json=platform_payload, headers=admin_headers).json()
    platform_id = platform["id"]

    profile_payload = {
        "platform_id": platform_id,
        "username": f"dossier_profile_{uuid.uuid4().hex[:6]}",
        "display_name": "Dossier Profile",
        "status": "active",
        "visibility_level": "admin",
        "metadata": None,
    }
    profile = client.post("/profiles", json=profile_payload, headers=admin_headers).json()
    profile_id = profile["id"]
    client.post(
        f"/persons/{person_id}/profiles",
        json={"profile_id": profile_id, "note": "primary"},
        headers=admin_headers,
    )

    second_profile_payload = {
        "platform_id": platform_id,
        "username": f"dossier_profile_{uuid.uuid4().hex[:6]}",
        "display_name": "Visible Profile",
        "status": "active",
        "visibility_level": "user",
        "metadata": None,
    }
    second_profile = client.post("/profiles", json=second_profile_payload, headers=admin_headers).json()
    client.post(
        f"/persons/{person_id}/profiles",
        json={"profile_id": second_profile["id"], "note": "secondary"},
        headers=admin_headers,
    )

    # Notes
    client.post(
        f"/notes/by-person/{person_id}",
        json={"text": "Admin note", "visibility_level": "admin"},
        headers=admin_headers,
    )
    client.post(
        f"/notes/by-person/{person_id}",
        json={"text": "User note", "visibility_level": "user"},
        headers=admin_headers,
    )

    # Activities
    for idx in range(2):
        client.post(
            "/activities",
            json={
                "person_id": person_id,
                "activity_type": f"event_{idx}",
                "occurred_at": "2024-03-01T12:00:00Z",
                "notes": f"Activity {idx}",
                "visibility_level": "user" if idx == 0 else "admin",
            },
            headers=admin_headers,
        )

    return {
        "person_id": person_id,
        "platform_id": platform_id,
        "admin_headers": admin_headers,
    }


def _cleanup_bundle(client, bundle):
    admin_headers = bundle["admin_headers"]
    client.delete(f"/persons/{bundle['person_id']}", headers=admin_headers)
    client.delete(f"/platforms/{bundle['platform_id']}", headers=admin_headers)


def test_person_dossier_endpoint_respects_visibility(client):
    bundle = _create_person_bundle(client)
    person_id = bundle["person_id"]
    admin_headers = bundle["admin_headers"]
    user_headers = {"X-Test-Role": "user"}

    admin_resp = client.get(f"/persons/{person_id}/dossier", headers=admin_headers)
    assert admin_resp.status_code == 200
    admin_payload = admin_resp.json()
    assert admin_payload["person"]["id"] == person_id
    assert admin_payload["relations"]["profiles"]
    assert admin_payload["relations"]["notes"]
    assert admin_payload["relations"]["activities"]
    assert admin_payload["stats"]["notes"]["total"] >= 2
    etag = admin_resp.headers.get("etag")
    assert etag
    cached_resp = client.get(
        f"/persons/{person_id}/dossier",
        headers={**admin_headers, "If-None-Match": etag},
    )
    assert cached_resp.status_code == 304

    user_resp = client.get(f"/persons/{person_id}/dossier", headers=user_headers)
    assert user_resp.status_code == 200
    user_payload = user_resp.json()
    assert user_payload["relations"]["profiles"]
    assert all(profile["visibility_level"] == "user" for profile in user_payload["relations"]["profiles"])
    assert all(note["visibility_level"] == "user" for note in user_payload["relations"]["notes"])
    assert user_payload["stats"]["notes"]["total"] == len(user_payload["relations"]["notes"])

    pdf_resp = client.get(f"/persons/{person_id}/dossier.pdf", headers=admin_headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF")
    pdf_etag = pdf_resp.headers.get("etag")
    assert pdf_etag
    cached_pdf = client.get(
        f"/persons/{person_id}/dossier.pdf",
        headers={**admin_headers, "If-None-Match": pdf_etag},
    )
    assert cached_pdf.status_code == 304

    _cleanup_bundle(client, bundle)


def test_dossier_service_limits(client):
    bundle = _create_person_bundle(client)
    person_id = bundle["person_id"]
    dossier, _ = dossier_service.fetch_person_dossier(
        person_id,
        current_user={"id": 1, "role": "head_admin"},
        profile_limit=1,
        note_limit=1,
        activity_limit=1,
    )
    assert len(dossier["relations"]["profiles"]) == 1
    assert len(dossier["relations"]["notes"]) == 1
    assert len(dossier["relations"]["activities"]) == 1

    _cleanup_bundle(client, bundle)
