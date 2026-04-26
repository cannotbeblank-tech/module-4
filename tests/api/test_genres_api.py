from __future__ import annotations

import allure
import pytest

from api.api_manager import ApiManager
from db.db_helper import DBHelper


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.regression
@pytest.mark.db
@allure.epic("Cinescope")
@allure.feature("Genres API")
class TestGenresAPI:
    @pytest.mark.schema
    @allure.story("List genres")
    @allure.title("GET /genres returns all genres stored in the database")
    def test_get_genres_returns_all_db_genres(
        self,
        unauthorized_api_manager: ApiManager,
        db_helper: DBHelper,
    ):
        genres_response = unauthorized_api_manager.genres_api.get_genres()
        db_genres = db_helper.get_all_genres()

        response_pairs = sorted((genre.id, genre.name) for genre in genres_response.root)
        db_pairs = sorted((genre.id, genre.name) for genre in db_genres)

        assert response_pairs == db_pairs
