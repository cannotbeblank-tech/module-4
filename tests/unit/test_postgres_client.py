from __future__ import annotations

from unittest.mock import Mock

import pytest

from db.db_helper import DBHelper
from db.db_models import MovieDBModel, UserDBModel


@pytest.mark.unit
class TestDBHelper:
    def test_get_movie_by_id_returns_row(self):
        db_session = Mock()
        query = db_session.query.return_value
        filtered = query.filter.return_value
        movie = MovieDBModel(id=101, name="Movie")
        filtered.first.return_value = movie

        helper = DBHelper(db_session)
        result = helper.get_movie_by_id(101)

        assert result is movie
        db_session.query.assert_called_once_with(MovieDBModel)

    def test_get_movie_by_id_returns_none_when_row_is_absent(self):
        db_session = Mock()
        query = db_session.query.return_value
        filtered = query.filter.return_value
        filtered.first.return_value = None

        helper = DBHelper(db_session)
        movie = helper.get_movie_by_id(999)

        assert movie is None
        db_session.query.assert_called_once_with(MovieDBModel)

    def test_get_user_by_email_returns_row(self):
        db_session = Mock()
        query = db_session.query.return_value
        filtered = query.filter.return_value
        user = UserDBModel(email="user@example.com", roles=["USER"])
        filtered.first.return_value = user

        helper = DBHelper(db_session)
        result = helper.get_user_by_email("user@example.com")

        assert result is user
        db_session.query.assert_called_once_with(UserDBModel)

    def test_set_user_roles_updates_row(self, monkeypatch: pytest.MonkeyPatch):
        db_session = Mock()
        user = UserDBModel(email="user@example.com", roles=["USER"])
        helper = DBHelper(db_session)
        monkeypatch.setattr(helper, "get_user_by_email", lambda _email: user)

        updated_user = helper.set_user_roles("user@example.com", ["ADMIN"])

        assert updated_user is user
        assert user.roles == ["ADMIN"]
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once_with(user)

    def test_delete_user_deletes_model(self):
        db_session = Mock()
        user = UserDBModel(email="user@example.com", roles=["USER"])
        helper = DBHelper(db_session)

        helper.delete_user(user)

        db_session.delete.assert_called_once_with(user)
        db_session.commit.assert_called_once()
