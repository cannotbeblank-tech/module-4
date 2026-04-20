from __future__ import annotations

import pytest
import requests

from api.api_manager import ApiManager
from constants import ADMIN_EMAIL, ADMIN_PASSWORD, SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD
from db.postgres_client import PostgresClient
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
    postgres_client: PostgresClient,
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
        deleted_rows = postgres_client.delete_user_by_email(user_data["email"])
        assert deleted_rows == 1


@pytest.fixture()
def admin_user_session() -> requests.Session:
    http_session = requests.Session()
    yield http_session
    http_session.close()


@pytest.fixture()
def admin_api_manager(
    admin_user_session: requests.Session,
    super_admin_api_manager: ApiManager,
    postgres_client: PostgresClient,
) -> ApiManager:
    user_data = DataGenerator.generate_user_data(role="USER")
    created_user = super_admin_api_manager.user_api.create_user(user_data).json()
    assert created_user["roles"] == ["USER"]

    patched_user = postgres_client.set_user_roles(user_data["email"], ["ADMIN"])
    assert patched_user is not None
    assert "ADMIN" in patched_user["roles"]

    manager = ApiManager(admin_user_session)
    try:
        login_payload = manager.auth_api.authenticate((user_data["email"], user_data["password"]))
        assert login_payload["user"]["roles"] == ["ADMIN"]
        manager.user_email = user_data["email"]
        manager.user_roles = ["ADMIN"]
        yield manager
    finally:
        deleted_rows = postgres_client.delete_user_by_email(user_data["email"])
        assert deleted_rows == 1


@pytest.fixture(scope="session")
def postgres_client() -> PostgresClient:
    if not PostgresClient.is_configured():
        pytest.skip("DB credentials are not configured in .env")

    client = PostgresClient()
    yield client
    client.close()


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
def created_movie_with_deletion(api_manager: ApiManager, movie_payload: dict) -> dict:
    response = api_manager.movies_api.create_movie(movie_payload)
    movie = response.json()
    yield movie

    movie_id = movie.get("id")
    if movie_id is not None:
        api_manager.movies_api.delete_movie(movie_id, expected_status=200)


@pytest.fixture()
def created_movie(api_manager: ApiManager, movie_payload: dict) -> dict:
    return api_manager.movies_api.create_movie(movie_payload).json()
