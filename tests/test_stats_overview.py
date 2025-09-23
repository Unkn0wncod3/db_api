from datetime import datetime


def test_stats_overview_caches_and_returns_structure(client):
    refresh_resp = client.get("/stats/overview", params={"force_refresh": True})
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()

    assert "meta" in data
    assert data["meta"]["cache_hit"] is False
    assert "generated_at" in data["meta"]
    assert "entities" in data
    assert "recent" in data
    assert "persons" in data["entities"]
    assert "total" in data["entities"]["persons"]

    # Subsequent call should hit the cache and reuse the same timestamp.
    cached_resp = client.get("/stats/overview")
    assert cached_resp.status_code == 200
    cached_data = cached_resp.json()
    assert cached_data["meta"]["cache_hit"] is True
    assert cached_data["meta"]["generated_at"] == data["meta"]["generated_at"]

    # ISO timestamps should parse without error (sanity check)
    datetime.fromisoformat(data["meta"]["generated_at"])
    datetime.fromisoformat(cached_data["meta"]["expires_at"])
