def test_create_person_requires_names(client):
    response = client.post('/persons', json={})
    assert response.status_code == 422
    detail = response.json().get('detail', [])
    assert detail, 'FastAPI sollte Validierungsfehler zurueckgeben'
    fields = {err['loc'][-1] for err in detail if err.get('loc')}
    assert {'first_name', 'last_name'} <= fields

