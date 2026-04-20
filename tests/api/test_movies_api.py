from __future__ import annotations

from datetime import datetime, timezone

import allure
import pytest
import pytest_check as check

from api.api_manager import ApiManager
from db.postgres_client import PostgresClient
from data.data_generator import DataGenerator
from models.movie_models import MovieDetails, MovieListResponse, MovieSummary


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.flaky(reruns=2, reruns_delay=1)
@pytest.mark.movies
@allure.epic("Cinescope")
@allure.feature("Movies API")
class TestMoviesAPI:
    @staticmethod
    def _get_recent_movies(api_manager: ApiManager) -> list[dict]:
        return api_manager.movies_api.get_movies(
            params={"page": 1, "pageSize": 20, "createdAt": "desc"}
        ).json()["movies"]

    @staticmethod
    def _create_movie(
        api_manager: ApiManager,
        *,
        genre_id: int,
        location: str = "MSK",
        published: bool = True,
    ) -> dict:
        return api_manager.movies_api.create_movie(
            DataGenerator.generate_movie_data(
                genre_id=genre_id,
                location=location,
                published=published,
            )
        ).json()

    @pytest.mark.smoke
    @pytest.mark.schema
    @allure.story("List movies")
    @allure.title("GET /movies returns a paginated collection that matches the schema")
    def test_get_movies_returns_paginated_list(self, unauthorized_api_manager: ApiManager):
        with allure.step("Request the first page of movies"):
            response = unauthorized_api_manager.movies_api.get_movies(params={"page": 1, "pageSize": 10})
            payload = response.json()
            movies_page = MovieListResponse.model_validate(payload)

        with allure.step("Validate pagination metadata"):
            assert isinstance(payload, dict)
            assert movies_page.page == 1
            assert movies_page.pageSize == 10
            assert movies_page.count >= 0
            assert movies_page.pageCount >= 1

    @pytest.mark.regression
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("filter_location", "other_location"),
        [("SPB", "MSK"), ("MSK", "SPB")],
        ids=["spb-filter", "msk-filter"],
    )
    @allure.story("Filter movies")
    @allure.title("GET /movies filters records by location: {filter_location}")
    def test_get_movies_filters_by_locations(
        self,
        api_manager: ApiManager,
        existing_genre_id: int,
        filter_location: str,
        other_location: str,
    ):
        with allure.step(f"Create movies for {filter_location} and {other_location}"):
            filtered_movie = api_manager.movies_api.create_movie(
                DataGenerator.generate_movie_data(location=filter_location, genre_id=existing_genre_id)
            ).json()
            other_movie = api_manager.movies_api.create_movie(
                DataGenerator.generate_movie_data(location=other_location, genre_id=existing_genre_id)
            ).json()

        with allure.step(f"Filter movies by {filter_location}"):
            response = api_manager.movies_api.get_movies(
                params={"locations": [filter_location], "page": 1, "pageSize": 20, "createdAt": "desc"}
            )
            payload = response.json()
            movies_page = MovieListResponse.model_validate(payload)
            returned_ids = {movie.id for movie in movies_page.movies}

        with allure.step("Verify that only the requested location is returned"):
            assert filtered_movie["id"] in returned_ids, "Созданный фильм должен попасть в выборку"
            assert all(movie.location == filter_location for movie in movies_page.movies)
            assert other_movie["id"] not in returned_ids, "Фильм с другой локацией не должен попасть в выборку"

        with allure.step("Delete test data"):
            api_manager.movies_api.delete_movie(filtered_movie["id"], expected_status=200)
            api_manager.movies_api.delete_movie(other_movie["id"], expected_status=200)

    @pytest.mark.regression
    @pytest.mark.slow
    @pytest.mark.parametrize("published", [True, False], ids=["published", "unpublished"])
    @allure.story("Filter movies")
    @allure.title("GET /movies filters records by published={published}")
    def test_get_movies_filters_by_published_flag(
        self,
        api_manager: ApiManager,
        existing_genre_id: int,
        published: bool,
    ):
        with allure.step(f"Create control data for published={published}"):
            expected_movie = self._create_movie(
                api_manager,
                genre_id=existing_genre_id,
                published=published,
            )
            other_movie = self._create_movie(
                api_manager,
                genre_id=existing_genre_id,
                published=not published,
            )

        with allure.step(f"Request movies with published={published}"):
            response = api_manager.movies_api.get_movies(
                params={"published": str(published).lower(), "page": 1, "pageSize": 20, "createdAt": "desc"}
            )
            movies_page = MovieListResponse.model_validate(response.json())
            returned_ids = {movie.id for movie in movies_page.movies}

        with allure.step("Validate filter result"):
            assert expected_movie["id"] in returned_ids
            assert other_movie["id"] not in returned_ids
            assert all(movie.published is published for movie in movies_page.movies)

        with allure.step("Delete test data"):
            api_manager.movies_api.delete_movie(expected_movie["id"], expected_status=200)
            api_manager.movies_api.delete_movie(other_movie["id"], expected_status=200)

    @pytest.mark.smoke
    @pytest.mark.schema
    @allure.story("Get movie by id")
    @allure.title("GET /movies/{id} returns the created movie")
    def test_get_movie_by_id(
        self,
        api_manager: ApiManager,
        created_movie_with_deletion: dict,
    ):
        movie_id = created_movie_with_deletion["id"]

        with allure.step(f"Request movie {movie_id} by id"):
            response = api_manager.movies_api.get_movie(movie_id)
            movie = MovieDetails.model_validate(response.json())

        with allure.step("Validate the returned movie data"):
            assert movie.id == movie_id
            assert movie.name == created_movie_with_deletion["name"]
            assert movie.genreId == created_movie_with_deletion["genreId"]
            assert isinstance(movie.reviews, list)

    @pytest.mark.smoke
    @allure.story("Role model")
    @allure.title("Public clients can read movies by id")
    def test_public_user_can_get_movie_by_id(
        self,
        unauthorized_api_manager: ApiManager,
        created_movie_with_deletion: dict,
    ):
        movie_id = created_movie_with_deletion["id"]

        with allure.step("Request movie by id without authorization"):
            response = unauthorized_api_manager.movies_api.get_movie(movie_id)
            movie = MovieDetails.model_validate(response.json())

        with allure.step("Validate that public access is allowed for GET /movies/{id}"):
            assert movie.id == movie_id
            assert movie.name == created_movie_with_deletion["name"]
            assert movie.genreId == created_movie_with_deletion["genreId"]

    @pytest.mark.smoke
    @pytest.mark.schema
    @allure.story("Create movie")
    @allure.title("POST /movies creates a movie and returns a valid schema")
    def test_create_movie(self, api_manager: ApiManager, movie_payload: dict):
        with allure.step("Create a movie via API"):
            response = api_manager.movies_api.create_movie(movie_payload)
            movie = MovieSummary.model_validate(response.json())

        with allure.step("Fetch the created movie from the API"):
            persisted_movie = MovieDetails.model_validate(api_manager.movies_api.get_movie(movie.id).json())
            created_at = movie.createdAt

        with allure.step("Validate the created movie payload and persisted state"):
            check.equal(persisted_movie.id, movie.id)
            for actual_movie in (movie, persisted_movie):
                check.equal(actual_movie.name, movie_payload["name"])
                check.equal(actual_movie.price, movie_payload["price"])
                check.equal(actual_movie.description, movie_payload["description"])
                check.equal(str(actual_movie.imageUrl), movie_payload["imageUrl"])
                check.equal(actual_movie.location, movie_payload["location"])
                check.equal(actual_movie.published, movie_payload["published"])
                check.equal(actual_movie.genreId, movie_payload["genreId"])
            check.is_true(abs((datetime.now(timezone.utc) - created_at).total_seconds()) <= 10)
            check.equal(persisted_movie.createdAt, movie.createdAt)
            check.is_true(persisted_movie.rating >= 0)

        with allure.step("Delete the created movie"):
            api_manager.movies_api.delete_movie(movie.id, expected_status=200)

    @pytest.mark.regression
    @allure.story("Update movie")
    @allure.title("PATCH /movies/{id} updates movie fields")
    def test_update_movie(
        self,
        api_manager: ApiManager,
        created_movie_with_deletion: dict,
        movie_payload: dict,
    ):
        movie_id = created_movie_with_deletion["id"]
        patch_data = movie_payload.copy()
        patch_data.update(
            {
                "name": f"UPDATED {created_movie_with_deletion['name']}",
                "price": created_movie_with_deletion["price"] + 111,
                "description": "Updated description from autotest",
                "published": False,
            }
        )

        with allure.step(f"Update movie {movie_id}"):
            updated_movie = MovieSummary.model_validate(
                api_manager.movies_api.update_movie(
                    movie_id,
                    patch_data,
                    expected_status=200,
                ).json()
            )
            persisted_movie = MovieDetails.model_validate(api_manager.movies_api.get_movie(movie_id).json())

        with allure.step("Validate updated fields in API responses"):
            for movie in (updated_movie, persisted_movie):
                assert movie.id == movie_id
                assert movie.name == patch_data["name"]
                assert movie.price == patch_data["price"]
                assert movie.description == patch_data["description"]
                assert not movie.published

    @pytest.mark.smoke
    @pytest.mark.slow
    @allure.story("Delete movie")
    @allure.title("DELETE /movies/{id} removes the movie")
    def test_delete_movie(self, api_manager: ApiManager, created_movie: dict):
        movie = created_movie
        movie_id = movie["id"]

        with allure.step(f"Delete movie {movie_id}"):
            deleted_movie = MovieSummary.model_validate(
                api_manager.movies_api.delete_movie(movie_id, expected_status=200).json()
            )
            response = api_manager.movies_api.get_movie(movie_id, expected_status=404)
            payload = response.json()

        with allure.step("Validate deleted movie payload and 404 after deletion"):
            assert deleted_movie.id == movie_id
            assert deleted_movie.name == movie["name"]
            assert deleted_movie.price == movie["price"]
            assert deleted_movie.description == movie["description"]
            assert deleted_movie.location == movie["location"]
            assert deleted_movie.genreId == movie["genreId"]
            assert payload["message"] == "Фильм не найден"

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("Create movie")
    @allure.title("POST /movies rejects duplicate movie names")
    def test_create_movie_with_duplicate_name_error(
        self,
        api_manager: ApiManager,
        movie_payload: dict,
    ):
        with allure.step("Create the original movie"):
            created_movie = MovieSummary.model_validate(api_manager.movies_api.create_movie(movie_payload).json())

        with allure.step("Attempt to create a movie with the same name"):
            duplicate_response = api_manager.movies_api.create_movie(movie_payload, expected_status=409)
            duplicate_payload = duplicate_response.json()
            recent_movies = self._get_recent_movies(api_manager)
            matching_movies = [movie for movie in recent_movies if movie["name"] == movie_payload["name"]]

        with allure.step("Validate duplicate protection"):
            assert duplicate_payload["message"] == "Фильм с таким названием уже существует"
            assert len(matching_movies) == 1
            assert matching_movies[0]["id"] == created_movie.id

        with allure.step("Delete the original movie"):
            api_manager.movies_api.delete_movie(created_movie.id, expected_status=200)

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("Create movie")
    @allure.title("POST /movies rejects an invalid payload")
    def test_create_movie_with_invalid_payload_error(
        self,
        api_manager: ApiManager,
        invalid_movie_payload: dict,
    ):
        with allure.step("Send an invalid movie payload"):
            response = api_manager.movies_api.create_movie(
                invalid_movie_payload,
                expected_status=400,
            )
            payload = response.json()
            recent_movies = self._get_recent_movies(api_manager)
            matching_movies = [movie for movie in recent_movies if movie["name"] == invalid_movie_payload["name"]]

        with allure.step("Validate validation errors and absence of persistence"):
            assert payload["message"] == [
                "Неверная ссылка",
                "Поле location должно быть одним из: MSK, SPB",
            ]
            assert not matching_movies

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("List movies")
    @allure.title("GET /movies rejects a pageSize above the contract limit")
    def test_get_movies_with_too_large_page_size_error(self, api_manager: ApiManager):
        with allure.step("Request movies with pageSize above the documented maximum"):
            response = api_manager.movies_api.get_movies(
                params={"page": 1, "pageSize": 21},
                expected_status=400,
            )
            payload = response.json()

        with allure.step("Validate the pageSize max error message"):
            assert payload["message"] == ["Поле pageSize имеет максимальную величину 20"]

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("List movies")
    @allure.title("GET /movies rejects page values below 1")
    def test_get_movies_with_invalid_page_error(self, api_manager: ApiManager):
        with allure.step("Request movies with page=0"):
            response = api_manager.movies_api.get_movies(
                params={"page": 0, "pageSize": 1},
                expected_status=400,
            )
            payload = response.json()

        with allure.step("Validate the page error message"):
            assert payload["message"] == ["Поле page имеет минимальную величину 1"]

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("List movies")
    @allure.title("GET /movies rejects an invalid createdAt sort order")
    def test_get_movies_with_invalid_created_at_sort_error(self, api_manager: ApiManager):
        with allure.step("Request movies with an invalid sort order"):
            response = api_manager.movies_api.get_movies(
                params={"page": 1, "pageSize": 1, "createdAt": "invalid"},
                expected_status=400,
            )
            payload = response.json()

        with allure.step("Validate the generic bad request message"):
            assert payload["message"] == "Некорректные данные"

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("List movies")
    @allure.title("GET /movies validates pageSize")
    def test_get_movies_with_invalid_page_size_error(self, api_manager: ApiManager):
        with allure.step("Request movies with an invalid pageSize"):
            response = api_manager.movies_api.get_movies(
                params={"page": 1, "pageSize": 0},
                expected_status=400,
            )
            payload = response.json()

        with allure.step("Validate the pageSize error message"):
            assert payload["message"] == ["Поле pageSize имеет минимальную величину 1"]

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("Get movie by id")
    @allure.title("GET /movies/{id} returns 404 for a nonexistent movie")
    def test_get_movie_with_nonexistent_id_error(self, api_manager: ApiManager):
        with allure.step("Request a nonexistent movie by id"):
            response = api_manager.movies_api.get_movie(999999999, expected_status=404)
            payload = response.json()

        with allure.step("Validate the 404 response"):
            assert payload["message"] == "Фильм не найден"

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("Update movie")
    @allure.title("PATCH /movies/{id} returns 404 for a nonexistent movie")
    def test_update_movie_with_nonexistent_id_error(self, api_manager: ApiManager):
        patch_data = {"name": "ghost movie autotest"}
        with allure.step("Update a nonexistent movie"):
            response = api_manager.movies_api.update_movie(
                999999999,
                patch_data,
                expected_status=404,
            )
            payload = response.json()
            recent_movies = self._get_recent_movies(api_manager)
            matching_movies = [movie for movie in recent_movies if movie["name"] == patch_data["name"]]

        with allure.step("Validate the 404 response and lack of side effects"):
            assert payload["message"] == "Фильм не найден"
            assert not matching_movies

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("Delete movie")
    @allure.title("DELETE /movies/{id} returns 404 for a nonexistent movie")
    def test_delete_movie_with_nonexistent_id_error(self, api_manager: ApiManager):
        with allure.step("Delete a nonexistent movie"):
            response = api_manager.movies_api.delete_movie(999999999, expected_status=404)
            payload = response.json()

        with allure.step("Validate the 404 response"):
            assert payload["message"] == "Фильм не найден"

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("Role model")
    @allure.title("Unauthorized clients cannot create movies")
    def test_unauthorized_user_cannot_create_movie(
        self,
        unauthorized_api_manager: ApiManager,
        existing_genre_id: int,
    ):
        with allure.step("Send POST /movies without authorization"):
            response = unauthorized_api_manager.movies_api.create_movie(
                DataGenerator.generate_movie_data(genre_id=existing_genre_id),
                expected_status=401,
            )
            payload = response.json()

        with allure.step("Validate 401 Unauthorized"):
            assert payload["message"] == "Unauthorized"

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("Role model")
    @allure.title("Unauthorized clients cannot update movies")
    def test_unauthorized_user_cannot_update_movie(
        self,
        unauthorized_api_manager: ApiManager,
        created_movie_with_deletion: dict,
    ):
        with allure.step("Send PATCH /movies/{id} without authorization"):
            response = unauthorized_api_manager.movies_api.update_movie(
                created_movie_with_deletion["id"],
                {"name": "unauthorized update"},
                expected_status=401,
            )
            payload = response.json()

        with allure.step("Validate 401 Unauthorized"):
            assert payload["message"] == "Unauthorized"

    @pytest.mark.regression
    @pytest.mark.negative
    @allure.story("Role model")
    @allure.title("Unauthorized clients cannot delete movies")
    def test_unauthorized_user_cannot_delete_movie(
        self,
        unauthorized_api_manager: ApiManager,
        created_movie_with_deletion: dict,
    ):
        with allure.step("Send DELETE /movies/{id} without authorization"):
            response = unauthorized_api_manager.movies_api.delete_movie(
                created_movie_with_deletion["id"],
                expected_status=401,
            )
            payload = response.json()

        with allure.step("Validate 401 Unauthorized"):
            assert payload["message"] == "Unauthorized"

    @pytest.mark.regression
    @pytest.mark.db
    @pytest.mark.slow
    @allure.story("Create movie")
    @allure.title("Created movie is persisted in the database")
    def test_created_movie_is_persisted_in_db(
        self,
        api_manager: ApiManager,
        created_movie_with_deletion: dict,
        postgres_client: PostgresClient,
    ):
        movie_id = created_movie_with_deletion["id"]

        with allure.step(f"Fetch movie {movie_id} from the database"):
            db_movie = postgres_client.get_movie_by_id(movie_id)

        with allure.step("Validate DB state against the API payload"):
            assert db_movie is not None, "Фильм должен существовать в базе данных"
            assert db_movie["id"] == movie_id
            assert db_movie["name"] == created_movie_with_deletion["name"]
            assert db_movie["description"] == created_movie_with_deletion["description"]
            assert db_movie["price"] == created_movie_with_deletion["price"]
            assert db_movie["location"] == created_movie_with_deletion["location"]
            assert db_movie["published"] == created_movie_with_deletion["published"]
            assert db_movie["genreId"] == created_movie_with_deletion["genreId"]

    @pytest.mark.regression
    @allure.story("Role model")
    @allure.title("A USER cannot create a movie while a SUPER_ADMIN can")
    def test_user_role_cannot_create_movie_but_super_admin_can(
        self,
        common_user_api_manager: ApiManager,
        super_admin_api_manager: ApiManager,
        existing_genre_id: int,
    ):
        movie_payload = DataGenerator.generate_movie_data(genre_id=existing_genre_id)

        with allure.step("Verify that a USER cannot create a movie"):
            user_response = common_user_api_manager.movies_api.create_movie(
                movie_payload,
                expected_status=403,
            )
            user_payload = user_response.json()

        with allure.step("Verify that a SUPER_ADMIN can create the same movie payload"):
            created_movie = MovieSummary.model_validate(
                super_admin_api_manager.movies_api.create_movie(movie_payload).json()
            )

        with allure.step("Validate both role outcomes"):
            assert user_payload["message"] == "Forbidden resource"
            assert created_movie.name == movie_payload["name"]
            assert created_movie.genreId == movie_payload["genreId"]

        with allure.step("Delete the movie created by the SUPER_ADMIN"):
            super_admin_api_manager.movies_api.delete_movie(created_movie.id, expected_status=200)

    @pytest.mark.regression
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("actor_fixture", "expected_status"),
        [
            ("common_user_api_manager", 403),
            ("admin_api_manager", 403),
            ("super_admin_api_manager", 200),
        ],
        ids=["user-forbidden", "admin-forbidden", "super-admin-allowed"],
    )
    @allure.story("Role model")
    @allure.title("DELETE /movies/{{id}} respects role permissions for {actor_fixture}")
    def test_delete_movie_respects_role_permissions(
        self,
        request: pytest.FixtureRequest,
        super_admin_api_manager: ApiManager,
        existing_genre_id: int,
        actor_fixture: str,
        expected_status: int,
    ):
        with allure.step("Create a movie using SUPER_ADMIN"):
            created_movie = self._create_movie(super_admin_api_manager, genre_id=existing_genre_id)
            movie_id = created_movie["id"]

        actor = request.getfixturevalue(actor_fixture)

        with allure.step(f"Attempt to delete movie {movie_id} as {actor_fixture}"):
            response = actor.movies_api.delete_movie(movie_id, expected_status=expected_status)

        with allure.step("Validate role-based delete behavior"):
            if expected_status == 403:
                payload = response.json()
                assert payload["message"] == "Forbidden resource"
                persisted_movie = MovieDetails.model_validate(
                    super_admin_api_manager.movies_api.get_movie(movie_id).json()
                )
                assert persisted_movie.id == movie_id
                super_admin_api_manager.movies_api.delete_movie(movie_id, expected_status=200)
            else:
                deleted_movie = MovieSummary.model_validate(response.json())
                assert deleted_movie.id == movie_id
                not_found_response = super_admin_api_manager.movies_api.get_movie(movie_id, expected_status=404)
                assert not_found_response.json()["message"] == "Фильм не найден"
