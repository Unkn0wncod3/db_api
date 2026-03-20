import pytest

CASES = [
    ("GET", "/", 200),
    ("GET", "/dashboard", 200),
    ("GET", "/history", 200),
    ("GET", "/schemas", 200),
    ("GET", "/entries", 200),
    ("GET", "/users", 200),
    ("GET", "/auth/me", 200),
]

@pytest.mark.parametrize("method,path,expected", CASES)
def test_endpoints_basic(client, method, path, expected):
    r = client.request(method, path)
    assert r.status_code != 404, f"{path} not found"
    assert r.status_code != 405, f"{path} method not allowed"
    assert r.status_code == expected
