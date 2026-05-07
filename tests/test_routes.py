def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok", "service": "urlshortener"}


def test_healthz_ok(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json()["db"] == "ok"


def test_shorten_creates_code(client, store):
    resp = client.post("/shorten", json={"url": "example.com"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["short_code"]
    assert body["short_url"].endswith("/" + body["short_code"])
    assert body["short_url"].startswith("http://test.local/")
    assert store[body["short_code"]]["original_url"] == "https://example.com"


def test_shorten_dedupe(client):
    first = client.post("/shorten", json={"url": "https://example.com"}).get_json()
    second = client.post("/shorten", json={"url": "https://example.com/"}).get_json()
    assert first["short_code"] == second["short_code"]


def test_shorten_missing_body(client):
    resp = client.post("/shorten", data="not json", content_type="text/plain")
    assert resp.status_code == 400


def test_shorten_invalid_url(client):
    resp = client.post("/shorten", json={"url": "not a url"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_shorten_missing_url_field(client):
    resp = client.post("/shorten", json={})
    assert resp.status_code == 400


def test_redirect_increments_click_count(client, store):
    create = client.post("/shorten", json={"url": "https://example.com"}).get_json()
    code = create["short_code"]
    resp = client.get(f"/{code}", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://example.com"
    assert store[code]["click_count"] == 1


def test_redirect_unknown_code(client):
    resp = client.get("/abc123")
    assert resp.status_code == 404


def test_redirect_invalid_code(client):
    resp = client.get("/has!chars")
    assert resp.status_code in (400, 404)


def test_api_key_required(app_with_api_key):
    client = app_with_api_key.test_client()
    resp = client.post("/shorten", json={"url": "example.com"})
    assert resp.status_code == 401

    resp = client.post(
        "/shorten",
        json={"url": "example.com"},
        headers={"X-API-Key": "secret-key"},
    )
    assert resp.status_code == 201

    resp = client.post(
        "/shorten",
        json={"url": "example.com"},
        headers={"X-API-Key": "wrong"},
    )
    assert resp.status_code == 401
