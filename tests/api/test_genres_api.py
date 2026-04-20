from __future__ import annotations

import allure
import pytest

from api.api_manager import ApiManager
from models.genre_models import GenreResponse


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.flaky(reruns=2, reruns_delay=1)
@pytest.mark.regression
@allure.epic("Cinescope")
@allure.feature("Genres API")
class TestGenresAPI:
    @pytest.mark.schema
    @allure.story("List genres")
    @allure.title("GET /genres returns a non-empty schema-valid collection")
    def test_get_genres_returns_non_empty_list(self, unauthorized_api_manager: ApiManager):
        with allure.step("Request public genres list"):
            response = unauthorized_api_manager.genres_api.get_genres()
            genres = [GenreResponse.model_validate(item) for item in response.json()]

        with allure.step("Validate schema and response content"):
            assert genres
            assert all(genre.id > 0 for genre in genres)
            assert any(genre.name == "Драма" for genre in genres)
