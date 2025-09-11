import pytest

# (Methode, Pfad, erwarteter Status)
CASES = [
    ("GET", "/", 200),
    ("GET", "/persons", 200),
    ("GET", "/notes", 200),
    ("GET", "/platforms", 200),
    ("GET", "/profiles", 200),
    ("GET", "/vehicles", 200),
    ("GET", "/activities", 200),
    ("GET", "/views/person_timeline/1", 200),
]

@pytest.mark.parametrize("method,path,expected", CASES)
def test_endpoints_basic(client, method, path, expected):
    r = client.request(method, path)
    assert r.status_code != 404, f"{path} not found"
    assert r.status_code != 405, f"{path} method not allowed"
    assert r.status_code == expected
