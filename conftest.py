from __future__ import annotations

import pytest
import requests

from api.api_manager import ApiManager
from constants import ADMIN_EMAIL, ADMIN_PASSWORD
from data.data_generator import DataGenerator


@pytest.fixture(scope="session")
def session() -> requests.Session:
    http_session = requests.Session()
    yield http_session
    http_session.close()


@pytest.fixture(scope="session")
def api_manager(session: requests.Session) -> ApiManager:
    return ApiManager(session)


@pytest.fixture(scope="session", autouse=True)
def admin_auth(api_manager: ApiManager) -> None:
    api_manager.auth_api.authenticate((ADMIN_EMAIL, ADMIN_PASSWORD))


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
def created_movie(api_manager: ApiManager, movie_payload: dict) -> dict:
    response = api_manager.movies_api.create_movie(movie_payload)
    movie = response.json()
    yield movie

    movie_id = movie.get("id")
    if movie_id is not None:
        api_manager.movies_api.delete_movie(movie_id, expected_status=200)


@pytest.fixture()
def movie_for_deletion(api_manager: ApiManager, movie_payload: dict) -> dict:
    return api_manager.movies_api.create_movie(movie_payload).json()
