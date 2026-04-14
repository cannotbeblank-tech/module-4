from __future__ import annotations

from typing import Any

from constants import AUTH_BASE_URL, LOGIN_ENDPOINT, REGISTER_ENDPOINT
from custom_requester.custom_requester import CustomRequester


class AuthAPI(CustomRequester):

    def __init__(self, session) -> None:
        super().__init__(session=session, base_url=AUTH_BASE_URL)

    def register_user(
        self,
        user_data: dict[str, Any],
        expected_status: int = 201,
    ):
        return self.send_request(
            method="POST",
            endpoint=REGISTER_ENDPOINT,
            data=user_data,
            expected_status=expected_status,
        )

    def login_user(
        self,
        login_data: dict[str, Any],
        expected_status: int = 200,
    ):
        return self.send_request(
            method="POST",
            endpoint=LOGIN_ENDPOINT,
            data=login_data,
            expected_status=expected_status,
        )

    def authenticate(self, user_creds: tuple[str, str]) -> dict[str, Any]:
        login_data = {"email": user_creds[0], "password": user_creds[1]}
        response_json = self.login_user(login_data=login_data, expected_status=200).json()

        if "accessToken" not in response_json:
            raise KeyError("accessToken is missing in login response")

        token = response_json["accessToken"]
        self._update_session_headers(Authorization=f"Bearer {token}")
        return response_json
