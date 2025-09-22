

def test_vehicles_full_crud_flow(client):
    create_payload = {
        "label": "Test Vehicle",
        "make": "Tesla",
        "model": "Model 3",
        "build_year": 2023,
        "license_plate": "TEST-123",
        "vehicle_type": "car",
        "energy_type": "electric",
        "color": "white",
        "metadata": None,
    }
    create_resp = client.post("/vehicles", json=create_payload)
    assert create_resp.status_code == 201
    vehicle = create_resp.json()
    vehicle_id = vehicle["id"]
    assert vehicle["label"] == create_payload["label"]

    list_resp = client.get("/vehicles")
    assert list_resp.status_code == 200
    ids = [item["id"] for item in list_resp.json()["items"]]
    assert vehicle_id in ids

    update_payload = {"color": "black", "mileage_km": 1500}
    update_resp = client.patch(f"/vehicles/{vehicle_id}", json=update_payload)
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["color"] == "black"
    assert updated["mileage_km"] == 1500

    delete_resp = client.delete(f"/vehicles/{vehicle_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] == vehicle_id

    missing_resp = client.patch(f"/vehicles/{vehicle_id}", json={"color": "silver"})
    assert missing_resp.status_code == 404
