from __future__ import annotations

from datetime import datetime, timezone

from api.api_manager import ApiManager
from data.data_generator import DataGenerator


class TestMoviesAPI:
    @staticmethod
    def _get_recent_movies(api_manager: ApiManager) -> list[dict]:
        return api_manager.movies_api.get_movies(
            params={"page": 1, "pageSize": 20, "createdAt": "desc"}
        ).json()["movies"]

    def test_get_movies_returns_paginated_list(self, api_manager: ApiManager):
        response = api_manager.movies_api.get_movies(params={"page": 1, "pageSize": 10})
        payload = response.json()

        assert isinstance(payload, dict)
        assert {"movies", "count", "page", "pageSize", "pageCount"}.issubset(payload.keys())
        assert isinstance(payload["movies"], list)
        assert payload["page"] == 1
        assert payload["pageSize"] == 10

    def test_get_movies_filters_by_locations(self, api_manager: ApiManager, existing_genre_id: int):
        spb_movie = api_manager.movies_api.create_movie(
            DataGenerator.generate_movie_data(location="SPB", genre_id=existing_genre_id)
        ).json()
        msk_movie = api_manager.movies_api.create_movie(
            DataGenerator.generate_movie_data(location="MSK", genre_id=existing_genre_id)
        ).json()

        response = api_manager.movies_api.get_movies(
            params={"locations": ["SPB"], "page": 1, "pageSize": 20, "createdAt": "desc"}
        )
        payload = response.json()
        movies = payload["movies"]
        returned_ids = {movie["id"] for movie in movies}

        assert spb_movie["id"] in returned_ids, "Созданный SPB-фильм должен попасть в выборку"
        assert all(movie["location"] == "SPB" for movie in movies), "Фильтр должен вернуть только SPB"
        assert msk_movie["id"] not in returned_ids, "MSK-фильм не должен попасть в фильтр SPB"

        api_manager.movies_api.delete_movie(spb_movie["id"], expected_status=200)
        api_manager.movies_api.delete_movie(msk_movie["id"], expected_status=200)

    def test_get_movie_by_id(
        self,
        api_manager: ApiManager,
        created_movie_with_deletion: dict,
    ):
        movie_id = created_movie_with_deletion["id"]

        response = api_manager.movies_api.get_movie(movie_id)
        movie = response.json()

        assert movie["id"] == movie_id
        assert movie["name"] == created_movie_with_deletion["name"]
        assert movie["genreId"] == created_movie_with_deletion["genreId"]
        assert "reviews" in movie

    def test_create_movie(self, api_manager: ApiManager, movie_payload: dict):
        response = api_manager.movies_api.create_movie(movie_payload)
        movie = response.json()
        persisted_movie = api_manager.movies_api.get_movie(movie["id"]).json()
        created_at = datetime.fromisoformat(movie["createdAt"].replace("Z", "+00:00"))

        assert persisted_movie["id"] == movie["id"]
        for actual_movie in (movie, persisted_movie):
            assert actual_movie["name"] == movie_payload["name"]
            assert actual_movie["price"] == movie_payload["price"]
            assert actual_movie["description"] == movie_payload["description"]
            assert actual_movie["imageUrl"] == movie_payload["imageUrl"]
            assert actual_movie["location"] == movie_payload["location"]
            assert actual_movie["published"] == movie_payload["published"]
            assert actual_movie["genreId"] == movie_payload["genreId"]
        assert abs((datetime.now(timezone.utc) - created_at).total_seconds()) <= 10
        assert persisted_movie["createdAt"] == movie["createdAt"]
        assert "rating" in persisted_movie

        api_manager.movies_api.delete_movie(movie["id"], expected_status=200)

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

        updated_movie = api_manager.movies_api.update_movie(
            movie_id,
            patch_data,
            expected_status=200,
        ).json()
        persisted_movie = api_manager.movies_api.get_movie(movie_id).json()

        for movie in (updated_movie, persisted_movie):
            assert movie["id"] == movie_id
            assert movie["name"] == patch_data["name"]
            assert movie["price"] == patch_data["price"]
            assert movie["description"] == patch_data["description"]
            assert not movie["published"]

    def test_delete_movie(self, api_manager: ApiManager, created_movie: dict):
        movie = created_movie
        movie_id = movie["id"]

        deleted_movie = api_manager.movies_api.delete_movie(movie_id, expected_status=200).json()
        response = api_manager.movies_api.get_movie(movie_id, expected_status=404)
        payload = response.json()

        assert deleted_movie["id"] == movie_id
        assert deleted_movie["name"] == movie["name"]
        assert deleted_movie["price"] == movie["price"]
        assert deleted_movie["description"] == movie["description"]
        assert deleted_movie["location"] == movie["location"]
        assert deleted_movie["genreId"] == movie["genreId"]
        assert payload["message"] == "Фильм не найден"

    def test_create_movie_with_duplicate_name_error(
        self,
        api_manager: ApiManager,
        movie_payload: dict,
    ):
        created_movie = api_manager.movies_api.create_movie(movie_payload).json()

        duplicate_response = api_manager.movies_api.create_movie(movie_payload, expected_status=409)
        duplicate_payload = duplicate_response.json()
        recent_movies = self._get_recent_movies(api_manager)
        matching_movies = [movie for movie in recent_movies if movie["name"] == movie_payload["name"]]

        assert duplicate_payload["message"] == "Фильм с таким названием уже существует"
        assert len(matching_movies) == 1
        assert matching_movies[0]["id"] == created_movie["id"]

        api_manager.movies_api.delete_movie(created_movie["id"], expected_status=200)

    def test_create_movie_with_invalid_payload_error(
        self,
        api_manager: ApiManager,
        invalid_movie_payload: dict,
    ):
        response = api_manager.movies_api.create_movie(
            invalid_movie_payload,
            expected_status=400,
        )
        payload = response.json()
        recent_movies = self._get_recent_movies(api_manager)
        matching_movies = [movie for movie in recent_movies if movie["name"] == invalid_movie_payload["name"]]

        assert payload["message"] == [
            "Неверная ссылка",
            "Поле location должно быть одним из: MSK, SPB",
        ]
        assert not matching_movies

    def test_get_movies_with_invalid_page_size_error(self, api_manager: ApiManager):
        response = api_manager.movies_api.get_movies(
            params={"page": 1, "pageSize": 0},
            expected_status=400,
        )
        payload = response.json()

        assert payload["message"] == ["Поле pageSize имеет минимальную величину 1"]

    def test_get_movie_with_nonexistent_id_error(self, api_manager: ApiManager):
        response = api_manager.movies_api.get_movie(999999999, expected_status=404)
        payload = response.json()

        assert payload["message"] == "Фильм не найден"

    def test_update_movie_with_nonexistent_id_error(self, api_manager: ApiManager):
        patch_data = {"name": "ghost movie autotest"}
        response = api_manager.movies_api.update_movie(
            999999999,
            patch_data,
            expected_status=404,
        )
        payload = response.json()
        recent_movies = self._get_recent_movies(api_manager)
        matching_movies = [movie for movie in recent_movies if movie["name"] == patch_data["name"]]

        assert payload["message"] == "Фильм не найден"
        assert not matching_movies

    def test_delete_movie_with_nonexistent_id_error(self, api_manager: ApiManager):
        response = api_manager.movies_api.delete_movie(999999999, expected_status=404)
        payload = response.json()

        assert payload["message"] == "Фильм не найден"
