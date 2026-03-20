def test_create_schema_requires_stable_key_and_name(client):
    response = client.post("/schemas", json={})
    assert response.status_code == 422
    detail = response.json().get("detail", [])
    assert detail
    fields = {err["loc"][-1] for err in detail if err.get("loc")}
    assert {"key", "name"} <= fields

