from __future__ import annotations

from typing import Any

from constants import AUTH_BASE_URL, USER_ENDPOINT
from custom_requester.custom_requester import CustomRequester


class UserAPI(CustomRequester):

    def __init__(self, session) -> None:
        super().__init__(session=session, base_url=AUTH_BASE_URL)

    def get_user(
        self,
        user_locator: str,
        expected_status: int = 200,
        response_model=None,
    ):
        return self.send_request(
            method="GET",
            endpoint=f"{USER_ENDPOINT}/{user_locator}",
            expected_status=expected_status,
            response_model=response_model,
        )

    def create_user(
        self,
        user_data: dict[str, Any],
        expected_status: int = 201,
        response_model=None,
    ):
        return self.send_request(
            method="POST",
            endpoint=USER_ENDPOINT,
            data=user_data,
            expected_status=expected_status,
            response_model=response_model,
        )
