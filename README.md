# urlshortener

A REST API that shortens URLs, built with Python, Flask, and PostgreSQL.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env  # then edit DB credentials
```

Create the database, then initialize the schema:

```bash
createdb urlshortener
python -c "from app.db import init_db; init_db()"
```

## Run

```bash
python -m app.main
```

The service listens on port `5001`.

## API

### `POST /shorten`

```json
{ "url": "https://example.com/some/path" }
```

Response `201`:

```json
{ "short_code": "aB3xYz", "short_url": "http://localhost:5001/aB3xYz" }
```

If the URL was already shortened, returns `200` with the existing code.

If `API_KEY` is set in the environment, requests must include
`X-API-Key: <value>`.

### `GET /<short_code>`

`302` redirect to the original URL. Increments `click_count`.

### `GET /healthz`

Liveness + DB connectivity check.

## Configuration

See `.env.example` for the full list. Notable variables:

- `BASE_URL` — used when constructing `short_url` in responses
- `API_KEY` — when set, `/shorten` requires the `X-API-Key` header
- `RATE_LIMIT_SHORTEN` / `RATE_LIMIT_REDIRECT` — Flask-Limiter syntax
  (e.g. `20 per minute`)

## Tests

```bash
pytest
```
