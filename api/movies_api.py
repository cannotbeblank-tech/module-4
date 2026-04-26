from __future__ import annotations

from typing import Any

from constants import MOVIES_ENDPOINT, API_BASE_URL
from custom_requester.custom_requester import CustomRequester
from models.movie_models import (
    ErrorMovieDetails,
    ErrorMovieList,
    ErrorMovieSummary,
    MovieDetails,
    MovieListResponse,
    MovieSummary,
)


class MoviesAPI(CustomRequester):
    def __init__(self, session) -> None:
        super().__init__(session=session, base_url=API_BASE_URL)

    def get_movies(
        self,
        params: dict[str, Any] | None = None,
        expected_status: int = 200,
    ):
        return self._send_request(
            method="GET",
            endpoint=MOVIES_ENDPOINT,
            params=params,
            expected_status=expected_status,
            success_model=MovieListResponse,
            error_model=ErrorMovieList,
        )

    def get_movie(
        self,
        movie_id: int,
        expected_status: int = 200,
    ):
        return self._send_request(
            method="GET",
            endpoint=f"{MOVIES_ENDPOINT}/{movie_id}",
            expected_status=expected_status,
            success_model=MovieDetails,
            error_model=ErrorMovieDetails,
        )

    def create_movie(
        self,
        movie_data: dict[str, Any],
        expected_status: int = 201,
    ):
        return self._send_request(
            method="POST",
            endpoint=MOVIES_ENDPOINT,
            data=movie_data,
            expected_status=expected_status,
            success_model=MovieSummary,
            error_model=ErrorMovieSummary,
        )

    def update_movie(
        self,
        movie_id: int,
        movie_data: dict[str, Any],
        expected_status: int = 200,
        method: str = "PATCH",
    ):
        return self._send_request(
            method=method,
            endpoint=f"{MOVIES_ENDPOINT}/{movie_id}",
            data=movie_data,
            expected_status=expected_status,
            success_model=MovieSummary,
            error_model=ErrorMovieSummary,
        )

    def delete_movie(
        self,
        movie_id: int,
        expected_status: int = 200,
    ):
        return self._send_request(
            method="DELETE",
            endpoint=f"{MOVIES_ENDPOINT}/{movie_id}",
            expected_status=expected_status,
            success_model=MovieSummary,
            error_model=ErrorMovieSummary,
        )
