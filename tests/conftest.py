import pytest

from app import create_app
from app.config import TestConfig
from app import routes as routes_module


class FakeCursor:
    def __init__(self, store):
        self.store = store
        self._result = None

    def execute(self, sql, params=()):
        normalized = " ".join(sql.split()).lower()
        if normalized.startswith("select 1 from urls where short_code"):
            code = params[0]
            self._result = (1,) if code in self.store else None
        elif normalized.startswith("select short_code from urls where original_url"):
            url = params[0]
            self._result = next(
                ((c,) for c, e in self.store.items() if e["original_url"] == url),
                None,
            )
        elif normalized.startswith("insert into urls"):
            url, code = params
            self.store[code] = {"original_url": url, "click_count": 0}
            self._result = None
        elif normalized.startswith("update urls set click_count"):
            code = params[0]
            entry = self.store.get(code)
            if entry is not None:
                entry["click_count"] += 1
                self._result = (entry["original_url"],)
            else:
                self._result = None
        elif normalized.startswith("select 1"):
            self._result = (1,)
        else:
            self._result = None

    def fetchone(self):
        return self._result

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConn:
    def __init__(self, store):
        self.store = store
        self.closed = False

    def cursor(self):
        return FakeCursor(self.store)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def store():
    return {}


@pytest.fixture
def app(store, monkeypatch):
    monkeypatch.setattr(routes_module, "get_db", lambda: FakeConn(store))
    return create_app(TestConfig)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def app_with_api_key(store, monkeypatch):
    class _Cfg(TestConfig):
        API_KEY = "secret-key"

    monkeypatch.setattr(routes_module, "get_db", lambda: FakeConn(store))
    return create_app(_Cfg)
