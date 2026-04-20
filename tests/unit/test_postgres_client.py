from __future__ import annotations

import pytest

from db.postgres_client import PostgresClient


class _FakeCursor:
    def __init__(self, rows: list[dict | None]) -> None:
        self._rows = rows
        self.executed: list[tuple[object, tuple[object, ...]]] = []

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, query, params) -> None:
        self.executed.append((query, params))

    def fetchone(self):
        if self._rows:
            return self._rows.pop(0)
        return None


class _FakeConnection:
    def __init__(self, rows: list[dict | None]) -> None:
        self.autocommit = False
        self.cursor_instance = _FakeCursor(rows)

    def cursor(self):
        return self.cursor_instance

    def close(self) -> None:
        return None


@pytest.mark.unit
class TestPostgresClient:
    def test_get_movie_by_id_retries_until_row_is_found(self, monkeypatch: pytest.MonkeyPatch):
        fake_connection = _FakeConnection([None, None, {"id": 101, "name": "Movie"}])
        monkeypatch.setattr("db.postgres_client.psycopg2.connect", lambda **kwargs: fake_connection)
        monkeypatch.setattr("db.postgres_client.time.sleep", lambda *_args, **_kwargs: None)

        client = PostgresClient()
        movie = client.get_movie_by_id(101, retries=3, delay=0)

        assert movie == {"id": 101, "name": "Movie"}
        assert len(fake_connection.cursor_instance.executed) == 3

    def test_get_movie_by_id_returns_none_when_row_is_absent(self, monkeypatch: pytest.MonkeyPatch):
        fake_connection = _FakeConnection([None, None])
        monkeypatch.setattr("db.postgres_client.psycopg2.connect", lambda **kwargs: fake_connection)
        monkeypatch.setattr("db.postgres_client.time.sleep", lambda *_args, **_kwargs: None)

        client = PostgresClient()
        movie = client.get_movie_by_id(999, retries=2, delay=0)

        assert movie is None
        assert len(fake_connection.cursor_instance.executed) == 2

    def test_get_user_by_email_returns_row(self, monkeypatch: pytest.MonkeyPatch):
        fake_connection = _FakeConnection([{"email": "user@example.com", "roles": "{USER}"}])
        monkeypatch.setattr("db.postgres_client.psycopg2.connect", lambda **kwargs: fake_connection)

        client = PostgresClient()
        user = client.get_user_by_email("user@example.com")

        assert user == {"email": "user@example.com", "roles": ["USER"]}
        assert fake_connection.cursor_instance.executed[0][1] == ("user@example.com",)

    def test_set_user_roles_updates_row(self, monkeypatch: pytest.MonkeyPatch):
        fake_connection = _FakeConnection([{"email": "user@example.com", "roles": "{ADMIN}"}])
        monkeypatch.setattr("db.postgres_client.psycopg2.connect", lambda **kwargs: fake_connection)

        client = PostgresClient()
        user = client.set_user_roles("user@example.com", ["ADMIN"])

        assert user == {"email": "user@example.com", "roles": ["ADMIN"]}
        assert fake_connection.cursor_instance.executed[0][1] == (["ADMIN"], "user@example.com")

    def test_delete_user_by_email_returns_deleted_row_count(self, monkeypatch: pytest.MonkeyPatch):
        fake_connection = _FakeConnection([])
        fake_connection.cursor_instance.rowcount = 1
        monkeypatch.setattr("db.postgres_client.psycopg2.connect", lambda **kwargs: fake_connection)

        client = PostgresClient()
        deleted_rows = client.delete_user_by_email("user@example.com")

        assert deleted_rows == 1
        assert fake_connection.cursor_instance.executed[0][1] == ("user@example.com",)
