def test_routes_endpoint_lists_routes(client):
    r = client.get("/__routes")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    paths = {item["path"] for item in r.json()}
    assert "/" in paths
    assert "/schemas" in paths
    assert "/entries" in paths
    assert "/users" in paths

def test_openapi_contains_expected_prefixes(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    data = r.json()
    paths = data.get("paths", {})
    all_paths = set(paths.keys())

    expected_prefixes = [
        "/auth", "/users", "/schemas", "/entries",
    ]
    missing = []
    for prefix in expected_prefixes:
        if not any(p == prefix or p.startswith(prefix + "/") for p in all_paths):
            missing.append(prefix)

    assert not missing, f"Missing route prefixes: {missing}"
