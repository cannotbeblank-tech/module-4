from __future__ import annotations

from constants import API_BASE_URL, GENRES_ENDPOINT
from custom_requester.custom_requester import CustomRequester


class GenresAPI(CustomRequester):

    def __init__(self, session) -> None:
        super().__init__(session=session, base_url=API_BASE_URL)

    def get_genres(self, expected_status: int = 200):
        return self.send_request(
            method="GET",
            endpoint=GENRES_ENDPOINT,
            expected_status=expected_status,
        )
