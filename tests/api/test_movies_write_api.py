from __future__ import annotations

from datetime import datetime, timezone

import allure
import pytest
import pytest_check as check

from api.api_manager import ApiManager
from db.db_helper import DBHelper


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.movies
@allure.epic("Cinescope")
@allure.feature("Movies API")
class TestMoviesWriteAPI:
    @pytest.mark.smoke
    @pytest.mark.schema
    @pytest.mark.db
    @allure.story("Create movie")
    @allure.title("POST /movies creates a movie")
    def test_create_movie(
        self,
        api_manager: ApiManager,
        movie_payload: dict,
        db_helper: DBHelper,
        track_movie_id,
    ):
        movie = api_manager.movies_api.create_movie(movie_payload)
        track_movie_id(movie.id)
        db_movie = db_helper.get_movie_by_id(movie.id)

        assert db_movie is not None
        check.equal(movie.name, movie_payload["name"])
        check.equal(movie.price, movie_payload["price"])
        check.equal(movie.description, movie_payload["description"])
        check.equal(str(movie.image_url), movie_payload["imageUrl"])
        check.equal(movie.location, movie_payload["location"])
        check.equal(movie.published, movie_payload["published"])
        check.equal(movie.genre_id, movie_payload["genreId"])
        check.is_true(abs((datetime.now(timezone.utc) - movie.created_at).total_seconds()) <= 10)
        check.equal(db_movie.id, movie.id)
        check.equal(db_movie.name, movie_payload["name"])
        check.equal(db_movie.description, movie_payload["description"])
        check.equal(db_movie.price, movie_payload["price"])
        check.equal(db_movie.location, movie_payload["location"])
        check.equal(db_movie.published, movie_payload["published"])
        check.equal(db_movie.genre_id, movie_payload["genreId"])

    @pytest.mark.regression
    @pytest.mark.db
    @allure.story("Update movie")
    @allure.title("PATCH /movies/{id} updates movie fields")
    def test_update_movie(
        self,
        api_manager: ApiManager,
        created_movie: dict,
        movie_payload: dict,
        db_helper: DBHelper,
    ):
        patch_data = movie_payload.copy()
        patch_data.update(
            {
                "name": f"UPDATED {created_movie['name']}",
                "price": created_movie["price"] + 111,
                "description": "Updated description from autotest",
                "published": False,
            }
        )

        updated_movie = api_manager.movies_api.update_movie(
            created_movie["id"],
            patch_data,
            expected_status=200,
        )
        db_movie = db_helper.get_movie_by_id(created_movie["id"])

        assert updated_movie.id == created_movie["id"]
        assert updated_movie.name == patch_data["name"]
        assert updated_movie.price == patch_data["price"]
        assert updated_movie.description == patch_data["description"]
        assert updated_movie.published is False
        assert db_movie.name == patch_data["name"]
        assert db_movie.price == patch_data["price"]
        assert db_movie.description == patch_data["description"]
        assert db_movie.published is False

    @pytest.mark.smoke
    @pytest.mark.db
    @allure.story("Delete movie")
    @allure.title("DELETE /movies/{id} removes the movie")
    def test_delete_movie(
        self,
        api_manager: ApiManager,
        created_movie: dict,
        db_helper: DBHelper,
    ):
        deleted_movie = api_manager.movies_api.delete_movie(
            created_movie["id"],
            expected_status=200,
        )
        db_movie = db_helper.get_movie_by_id(created_movie["id"])

        assert deleted_movie.id == created_movie["id"]
        assert deleted_movie.name == created_movie["name"]
        assert deleted_movie.price == created_movie["price"]
        assert deleted_movie.description == created_movie["description"]
        assert deleted_movie.location == created_movie["location"]
        assert deleted_movie.genre_id == created_movie["genreId"]
        assert db_movie is None

    @pytest.mark.regression
    @pytest.mark.negative
    @pytest.mark.db
    @allure.story("Create movie")
    @allure.title("POST /movies rejects duplicate movie names")
    def test_create_movie_with_duplicate_name_error(
        self,
        api_manager: ApiManager,
        movie_payload: dict,
        db_helper: DBHelper,
        track_movie_id,
    ):
        created_movie = api_manager.movies_api.create_movie(movie_payload)
        track_movie_id(created_movie.id)
        duplicate_response = api_manager.movies_api.create_movie(movie_payload, expected_status=409)
        matching_movies = db_helper.get_movies_by_name(movie_payload["name"])

        assert duplicate_response.message == "Фильм с таким названием уже существует"
        assert len(matching_movies) == 1
        assert matching_movies[0].id == created_movie.id

    @pytest.mark.regression
    @pytest.mark.negative
    @pytest.mark.db
    @allure.story("Create movie")
    @allure.title("POST /movies rejects an invalid payload")
    def test_create_movie_with_invalid_payload_error(
        self,
        api_manager: ApiManager,
        invalid_movie_payload: dict,
        db_helper: DBHelper,
    ):
        response = api_manager.movies_api.create_movie(
            invalid_movie_payload,
            expected_status=400,
        )
        matching_movies = db_helper.get_movies_by_name(invalid_movie_payload["name"])

        assert response.message == [
            "Неверная ссылка",
            "Поле location должно быть одним из: MSK, SPB",
        ]
        assert not matching_movies

    @pytest.mark.regression
    @pytest.mark.negative
    @pytest.mark.db
    @allure.story("Update movie")
    @allure.title("PATCH /movies/{id} returns 404 for a nonexistent movie")
    def test_update_movie_with_nonexistent_id_error(
        self,
        api_manager: ApiManager,
        db_helper: DBHelper,
    ):
        patch_data = {"name": "ghost movie autotest"}

        response = api_manager.movies_api.update_movie(
            999999999,
            patch_data,
            expected_status=404,
        )
        matching_movies = db_helper.get_movies_by_name(patch_data["name"])

        assert response.message == "Фильм не найден"
        assert not matching_movies

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("Delete movie")
    @allure.title("DELETE /movies/{id} returns 404 for a nonexistent movie")
    def test_delete_movie_with_nonexistent_id_error(self, api_manager: ApiManager):
        response = api_manager.movies_api.delete_movie(999999999, expected_status=404)

        assert response.message == "Фильм не найден"
