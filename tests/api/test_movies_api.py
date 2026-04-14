from __future__ import annotations

from api.api_manager import ApiManager
from data.data_generator import DataGenerator


class TestMoviesAPI:
    def test_get_movies_returns_paginated_list(self, api_manager: ApiManager) -> None:
        response = api_manager.movies_api.get_movies(params={"page": 1, "pageSize": 10})
        payload = response.json()

        assert response.status_code == 200
        assert isinstance(payload, dict)
        assert {"movies", "count", "page", "pageSize", "pageCount"}.issubset(payload.keys())
        assert isinstance(payload["movies"], list)
        assert payload["page"] == 1
        assert payload["pageSize"] == 10

    def test_get_movies_filters_by_locations(self, api_manager: ApiManager, existing_genre_id: int) -> None:
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

        assert response.status_code == 200
        assert spb_movie["id"] in returned_ids, "Созданный SPB-фильм должен попасть в выборку"
        assert all(movie["location"] == "SPB" for movie in movies), "Фильтр должен вернуть только SPB"
        assert msk_movie["id"] not in returned_ids, "MSK-фильм не должен попасть в фильтр SPB"

        api_manager.movies_api.delete_movie(spb_movie["id"], expected_status=(200, 404))
        api_manager.movies_api.delete_movie(msk_movie["id"], expected_status=(200, 404))

    def test_get_movie_by_id(self, api_manager: ApiManager, created_movie: dict) -> None:
        movie_id = created_movie["id"]

        response = api_manager.movies_api.get_movie(movie_id)
        movie = response.json()

        assert response.status_code == 200
        assert movie["id"] == movie_id
        assert movie["name"] == created_movie["name"]
        assert movie["genreId"] == created_movie["genreId"]
        assert "reviews" in movie

    def test_create_movie(self, api_manager: ApiManager, movie_payload: dict) -> None:
        response = api_manager.movies_api.create_movie(movie_payload)
        movie = response.json()

        assert response.status_code == 201
        assert movie["name"] == movie_payload["name"]
        assert movie["price"] == movie_payload["price"]
        assert movie["description"] == movie_payload["description"]
        assert movie["location"] == movie_payload["location"]
        assert movie["genreId"] == movie_payload["genreId"]
        assert "id" in movie
        assert "createdAt" in movie
        assert "rating" in movie

        api_manager.movies_api.delete_movie(movie["id"], expected_status=(200, 404))

    def test_update_movie(self, api_manager: ApiManager, created_movie: dict) -> None:
        movie_id = created_movie["id"]
        patch_data = {
            "name": f"UPDATED {created_movie['name']}",
            "price": created_movie["price"] + 111,
            "description": "Updated description from autotest",
            "published": False,
        }

        response = api_manager.movies_api.update_movie(movie_id, patch_data, expected_status=200)
        movie = response.json()

        assert response.status_code == 200
        assert movie["id"] == movie_id
        assert movie["name"] == patch_data["name"]
        assert movie["price"] == patch_data["price"]
        assert movie["description"] == patch_data["description"]
        assert movie["published"] is False

    def test_delete_movie(self, api_manager: ApiManager, existing_genre_id: int) -> None:
        movie = api_manager.movies_api.create_movie(
            DataGenerator.generate_movie_data(genre_id=existing_genre_id)
        ).json()
        movie_id = movie["id"]

        delete_response = api_manager.movies_api.delete_movie(movie_id, expected_status=200)
        get_response = api_manager.movies_api.get_movie(movie_id, expected_status=404)

        assert delete_response.status_code == 200
        assert get_response.status_code == 404

    def test_create_movie_with_duplicate_name_returns_409(
        self,
        api_manager: ApiManager,
        movie_payload: dict,
    ) -> None:
        created_movie = api_manager.movies_api.create_movie(movie_payload).json()

        duplicate_response = api_manager.movies_api.create_movie(movie_payload, expected_status=409)

        assert duplicate_response.status_code == 409

        api_manager.movies_api.delete_movie(created_movie["id"], expected_status=(200, 404))

    def test_create_movie_with_invalid_payload_returns_400(
        self,
        api_manager: ApiManager,
        invalid_movie_payload: dict,
    ) -> None:
        response = api_manager.movies_api.create_movie(
            invalid_movie_payload,
            expected_status=400,
        )

        assert response.status_code == 400

    def test_get_movies_with_invalid_page_size_returns_400(self, api_manager: ApiManager) -> None:
        response = api_manager.movies_api.get_movies(
            params={"page": 1, "pageSize": 0},
            expected_status=400,
        )

        assert response.status_code == 400

    def test_get_movie_with_nonexistent_id_returns_404(self, api_manager: ApiManager) -> None:
        response = api_manager.movies_api.get_movie(999999999, expected_status=404)
        assert response.status_code == 404

    def test_update_movie_with_nonexistent_id_returns_404(self, api_manager: ApiManager) -> None:
        patch_data = {"name": "ghost movie"}
        response = api_manager.movies_api.update_movie(
            999999999,
            patch_data,
            expected_status=404,
        )

        assert response.status_code == 404

    def test_delete_movie_with_nonexistent_id_returns_404(self, api_manager: ApiManager) -> None:
        response = api_manager.movies_api.delete_movie(999999999, expected_status=404)
        assert response.status_code == 404
