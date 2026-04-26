from __future__ import annotations

import allure
import pytest

from api.api_manager import ApiManager
from db.db_helper import DBHelper
from data.data_generator import DataGenerator


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.movies
@allure.epic("Cinescope")
@allure.feature("Movies API")
class TestMoviesRoleAPI:
    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("Role model")
    @allure.title("Unauthorized clients cannot create movies")
    def test_unauthorized_user_cannot_create_movie(
        self,
        unauthorized_api_manager: ApiManager,
        existing_genre_id: int,
        db_helper: DBHelper,
    ):
        movie_payload = DataGenerator.generate_movie_data(genre_id=existing_genre_id)
        response = unauthorized_api_manager.movies_api.create_movie(
            movie_payload,
            expected_status=401,
        )
        matching_movies = db_helper.get_movies_by_name(movie_payload["name"])

        assert response.message == "Unauthorized"
        assert not matching_movies

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("Role model")
    @allure.title("Unauthorized clients cannot update movies")
    def test_unauthorized_user_cannot_update_movie(
        self,
        unauthorized_api_manager: ApiManager,
        created_movie: dict,
        db_helper: DBHelper,
    ):
        response = unauthorized_api_manager.movies_api.update_movie(
            created_movie["id"],
            {"name": "unauthorized update"},
            expected_status=401,
        )
        db_movie = db_helper.get_movie_by_id(created_movie["id"])

        assert response.message == "Unauthorized"
        assert db_movie is not None
        assert db_movie.name == created_movie["name"]

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("Role model")
    @allure.title("Unauthorized clients cannot delete movies")
    def test_unauthorized_user_cannot_delete_movie(
        self,
        unauthorized_api_manager: ApiManager,
        created_movie: dict,
        db_helper: DBHelper,
    ):
        response = unauthorized_api_manager.movies_api.delete_movie(
            created_movie["id"],
            expected_status=401,
        )
        db_movie = db_helper.get_movie_by_id(created_movie["id"])

        assert response.message == "Unauthorized"
        assert db_movie is not None
        assert db_movie.id == created_movie["id"]

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("Role model")
    @allure.title("USER cannot create a movie")
    def test_user_cannot_create_movie(
        self,
        common_user_api_manager: ApiManager,
        existing_genre_id: int,
        db_helper: DBHelper,
    ):
        movie_payload = DataGenerator.generate_movie_data(genre_id=existing_genre_id)
        response = common_user_api_manager.movies_api.create_movie(
            movie_payload,
            expected_status=403,
        )
        matching_movies = db_helper.get_movies_by_name(movie_payload["name"])

        assert response.message == "Forbidden resource"
        assert not matching_movies

    @pytest.mark.regression
    @allure.story("Role model")
    @allure.title("SUPER_ADMIN can create a movie")
    def test_super_admin_can_create_movie(
        self,
        super_admin_api_manager: ApiManager,
        existing_genre_id: int,
        db_helper: DBHelper,
        track_movie_id,
    ):
        movie_payload = DataGenerator.generate_movie_data(genre_id=existing_genre_id)

        created_movie = super_admin_api_manager.movies_api.create_movie(movie_payload)
        track_movie_id(created_movie.id)
        db_movie = db_helper.get_movie_by_id(created_movie.id)

        assert created_movie.name == movie_payload["name"]
        assert created_movie.genre_id == movie_payload["genreId"]
        assert db_movie is not None
        assert db_movie.name == movie_payload["name"]

    @pytest.mark.regression
    @pytest.mark.negative
    @pytest.mark.db
    @pytest.mark.parametrize(
        "actor_fixture",
        ["common_user_api_manager", "admin_api_manager"],
        ids=["user-forbidden", "admin-forbidden"],
    )
    @allure.story("Role model")
    @allure.title("USER and ADMIN cannot delete movies")
    def test_user_and_admin_cannot_delete_movie(
        self,
        request: pytest.FixtureRequest,
        super_admin_api_manager: ApiManager,
        movie_factory,
        db_helper: DBHelper,
        actor_fixture: str,
    ):
        created_movie = movie_factory(super_admin_api_manager)
        actor = request.getfixturevalue(actor_fixture)

        response = actor.movies_api.delete_movie(created_movie["id"], expected_status=403)
        db_movie = db_helper.get_movie_by_id(created_movie["id"])

        assert response.message == "Forbidden resource"
        assert db_movie is not None
        assert db_movie.id == created_movie["id"]

    @pytest.mark.regression
    @pytest.mark.db
    @allure.story("Role model")
    @allure.title("SUPER_ADMIN can delete movies")
    def test_super_admin_can_delete_movie(
        self,
        super_admin_api_manager: ApiManager,
        movie_factory,
        db_helper: DBHelper,
    ):
        created_movie = movie_factory(super_admin_api_manager)

        deleted_movie = super_admin_api_manager.movies_api.delete_movie(
            created_movie["id"],
            expected_status=200,
        )
        db_movie = db_helper.get_movie_by_id(created_movie["id"])

        assert deleted_movie.id == created_movie["id"]
        assert db_movie is None
