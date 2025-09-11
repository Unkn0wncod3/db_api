import pytest

def _get_all_get_paths_static():
    return [
        "/", "/persons", "/notes", "/platforms", "/profiles",
        "/vehicles", "/activities"
    ]

@pytest.mark.parametrize("path", _get_all_get_paths_static())
def test_all_gets_no_500(client, path):
    r = client.get(path)
    assert r.status_code < 500, f"GET {path} -> {r.status_code}"
