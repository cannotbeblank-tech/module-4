from __future__ import annotations

import pytest
import requests
from sqlalchemy.orm import Session

from api.api_manager import ApiManager
from constants import ADMIN_EMAIL, ADMIN_PASSWORD, SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD
from db import DBHelper, get_db_session
from data.data_generator import DataGenerator
@pytest.fixture(scope="session")
def session() -> requests.Session:
    http_session = requests.Session()
    yield http_session
    http_session.close()


@pytest.fixture(scope="session")
def api_manager(session: requests.Session) -> ApiManager:
    manager = ApiManager(session)
    manager.auth_api.authenticate((ADMIN_EMAIL, ADMIN_PASSWORD))
    return manager


@pytest.fixture()
def unauthorized_session() -> requests.Session:
    http_session = requests.Session()
    yield http_session
    http_session.close()


@pytest.fixture()
def unauthorized_api_manager(unauthorized_session: requests.Session) -> ApiManager:
    return ApiManager(unauthorized_session)


@pytest.fixture(scope="session")
def super_admin_session() -> requests.Session:
    http_session = requests.Session()
    yield http_session
    http_session.close()


@pytest.fixture(scope="session")
def super_admin_api_manager(super_admin_session: requests.Session) -> ApiManager:
    manager = ApiManager(super_admin_session)
    login_payload = manager.auth_api.authenticate((SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD))
    manager.user_email = SUPER_ADMIN_EMAIL
    manager.user_roles = login_payload["user"]["roles"]
    return manager


@pytest.fixture()
def common_user_session() -> requests.Session:
    http_session = requests.Session()
    yield http_session
    http_session.close()


@pytest.fixture()
def common_user_api_manager(
    common_user_session: requests.Session,
    super_admin_api_manager: ApiManager,
    db_helper: DBHelper,
) -> ApiManager:
    user_data = DataGenerator.generate_user_data(role="USER")
    created_user = super_admin_api_manager.user_api.create_user(user_data).json()
    assert created_user["email"] == user_data["email"]
    assert created_user["roles"] == ["USER"]

    manager = ApiManager(common_user_session)
    try:
        login_payload = manager.auth_api.authenticate((user_data["email"], user_data["password"]))
        manager.user_email = user_data["email"]
        manager.user_roles = login_payload["user"]["roles"]
        yield manager
    finally:
        user = db_helper.get_user_by_email(user_data["email"])
        assert user is not None
        db_helper.delete_user(user)


@pytest.fixture()
def admin_user_session() -> requests.Session:
    http_session = requests.Session()
    yield http_session
    http_session.close()


@pytest.fixture()
def admin_api_manager(
    admin_user_session: requests.Session,
    super_admin_api_manager: ApiManager,
    db_helper: DBHelper,
) -> ApiManager:
    user_data = DataGenerator.generate_user_data(role="USER")
    created_user = super_admin_api_manager.user_api.create_user(user_data).json()
    assert created_user["roles"] == ["USER"]

    patched_user = db_helper.set_user_roles(user_data["email"], ["ADMIN"])
    assert patched_user is not None
    assert "ADMIN" in patched_user.roles

    manager = ApiManager(admin_user_session)
    try:
        login_payload = manager.auth_api.authenticate((user_data["email"], user_data["password"]))
        assert login_payload["user"]["roles"] == ["ADMIN"]
        manager.user_email = user_data["email"]
        manager.user_roles = ["ADMIN"]
        yield manager
    finally:
        user = db_helper.get_user_by_email(user_data["email"])
        assert user is not None
        db_helper.delete_user(user)


@pytest.fixture(scope="module")
def db_session() -> Session:
    session = get_db_session()
    yield session
    session.close()


@pytest.fixture()
def db_helper(db_session: Session) -> DBHelper:
    return DBHelper(db_session)


@pytest.fixture(scope="session")
def existing_genre_id(api_manager: ApiManager) -> int:
    genres = api_manager.genres_api.get_genres().json()
    assert isinstance(genres, list) and genres, "GET /genres должен вернуть хотя бы один жанр"
    return genres[0]["id"]


@pytest.fixture()
def movie_payload(existing_genre_id: int) -> dict:
    return DataGenerator.generate_movie_data(genre_id=existing_genre_id)


@pytest.fixture()
def invalid_movie_payload() -> dict:
    return DataGenerator.generate_invalid_movie_data()


@pytest.fixture()
def movie_factory(super_admin_api_manager: ApiManager, existing_genre_id: int):
    created_movie_ids: list[int] = []

    def _factory(
        api_manager: ApiManager,
        *,
        genre_id: int | None = None,
        location: str | None = None,
        published: bool = True,
        payload: dict | None = None,
    ) -> dict:
        movie_payload = payload or DataGenerator.generate_movie_data(
            genre_id=genre_id or existing_genre_id,
            location=location,
            published=published,
        )
        movie = api_manager.movies_api.create_movie(movie_payload).json()
        created_movie_ids.append(movie["id"])
        return movie

    yield _factory

    for movie_id in reversed(created_movie_ids):
        super_admin_api_manager.movies_api.delete_movie(movie_id, expected_status=200)


@pytest.fixture()
def created_movie(api_manager: ApiManager, movie_factory) -> dict:
    return movie_factory(api_manager)
