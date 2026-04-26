from __future__ import annotations

import allure
import pytest

from api.api_manager import ApiManager


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.movies
@allure.epic("Cinescope")
@allure.feature("Movies API")
class TestMoviesReadAPI:
    @pytest.mark.smoke
    @pytest.mark.schema
    @allure.story("List movies")
    @allure.title("GET /movies returns a paginated collection")
    def test_get_movies_returns_paginated_list(self, unauthorized_api_manager: ApiManager):
        movies_page = unauthorized_api_manager.movies_api.get_movies(
            params={"page": 1, "pageSize": 10},
        )

        assert movies_page.page == 1
        assert movies_page.page_size == 10
        assert movies_page.count >= 0
        assert movies_page.page_count >= 1

    @pytest.mark.regression
    @pytest.mark.slow
    @pytest.mark.db
    @allure.story("Filter movies")
    @allure.title("GET /movies filters records by location")
    def test_get_movies_filters_by_locations(
        self,
        api_manager: ApiManager,
        movie_factory,
    ):
        filtered_movie = movie_factory(api_manager, location="SPB")
        other_movie = movie_factory(api_manager, location="MSK")

        movies_page = api_manager.movies_api.get_movies(
            params={"locations": ["SPB"], "page": 1, "pageSize": 20, "createdAt": "desc"},
        )
        returned_ids = {movie.id for movie in movies_page.movies}

        assert filtered_movie["id"] in returned_ids
        assert all(movie.location == "SPB" for movie in movies_page.movies)
        assert other_movie["id"] not in returned_ids

    @pytest.mark.regression
    @pytest.mark.slow
    @pytest.mark.db
    @allure.story("Filter movies")
    @allure.title("GET /movies returns only published movies")
    def test_get_movies_filters_published_movies(
        self,
        api_manager: ApiManager,
        movie_factory,
    ):
        published_movie = movie_factory(api_manager, published=True)
        unpublished_movie = movie_factory(api_manager, published=False)

        movies_page = api_manager.movies_api.get_movies(
            params={"published": "true", "page": 1, "pageSize": 20, "createdAt": "desc"},
        )
        returned_ids = {movie.id for movie in movies_page.movies}

        assert published_movie["id"] in returned_ids
        assert unpublished_movie["id"] not in returned_ids
        assert all(movie.published is True for movie in movies_page.movies)

    @pytest.mark.regression
    @pytest.mark.slow
    @pytest.mark.db
    @allure.story("Filter movies")
    @allure.title("GET /movies returns only unpublished movies")
    def test_get_movies_filters_unpublished_movies(
        self,
        api_manager: ApiManager,
        movie_factory,
    ):
        unpublished_movie = movie_factory(api_manager, published=False)
        published_movie = movie_factory(api_manager, published=True)

        movies_page = api_manager.movies_api.get_movies(
            params={"published": "false", "page": 1, "pageSize": 20, "createdAt": "desc"},
        )
        returned_ids = {movie.id for movie in movies_page.movies}

        assert unpublished_movie["id"] in returned_ids
        assert published_movie["id"] not in returned_ids
        assert all(movie.published is False for movie in movies_page.movies)

    @pytest.mark.smoke
    @pytest.mark.schema
    @allure.story("Get movie by id")
    @allure.title("GET /movies/{id} returns the created movie")
    def test_get_movie_by_id(
        self,
        api_manager: ApiManager,
        created_movie: dict,
    ):
        returned_movie = api_manager.movies_api.get_movie(created_movie["id"])

        assert returned_movie.id == created_movie["id"]
        assert returned_movie.name == created_movie["name"]
        assert returned_movie.genre_id == created_movie["genreId"]

    @pytest.mark.smoke
    @allure.story("Role model")
    @allure.title("Public clients can read movies by id")
    def test_public_user_can_get_movie_by_id(
        self,
        unauthorized_api_manager: ApiManager,
        created_movie: dict,
    ):
        returned_movie = unauthorized_api_manager.movies_api.get_movie(created_movie["id"])

        assert returned_movie.id == created_movie["id"]
        assert returned_movie.name == created_movie["name"]
        assert returned_movie.genre_id == created_movie["genreId"]

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("List movies")
    @allure.title("GET /movies rejects a pageSize above the contract limit")
    def test_get_movies_with_too_large_page_size_error(self, api_manager: ApiManager):
        response = api_manager.movies_api.get_movies(
            params={"page": 1, "pageSize": 21},
            expected_status=400,
        )

        assert response.message == ["Поле pageSize имеет максимальную величину 20"]

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("List movies")
    @allure.title("GET /movies rejects page values below 1")
    def test_get_movies_with_invalid_page_error(self, api_manager: ApiManager):
        response = api_manager.movies_api.get_movies(
            params={"page": 0, "pageSize": 1},
            expected_status=400,
        )

        assert response.message == ["Поле page имеет минимальную величину 1"]

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("List movies")
    @allure.title("GET /movies rejects an invalid createdAt sort order")
    def test_get_movies_with_invalid_created_at_sort_error(self, api_manager: ApiManager):
        response = api_manager.movies_api.get_movies(
            params={"page": 1, "pageSize": 1, "createdAt": "invalid"},
            expected_status=400,
        )

        assert response.message == "Некорректные данные"

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("List movies")
    @allure.title("GET /movies validates pageSize")
    def test_get_movies_with_invalid_page_size_error(self, api_manager: ApiManager):
        response = api_manager.movies_api.get_movies(
            params={"page": 1, "pageSize": 0},
            expected_status=400,
        )

        assert response.message == ["Поле pageSize имеет минимальную величину 1"]

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("Get movie by id")
    @allure.title("GET /movies/{id} returns 404 for a nonexistent movie")
    def test_get_movie_with_nonexistent_id_error(self, api_manager: ApiManager):
        response = api_manager.movies_api.get_movie(999999999, expected_status=404)

        assert response.message == "Фильм не найден"
