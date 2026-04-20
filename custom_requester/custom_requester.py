from __future__ import annotations

import json
import logging
from typing import Any, Iterable

import requests

from constants import DEFAULT_HEADERS


class CustomRequester:

    def __init__(self, session: requests.Session, base_url: str) -> None:
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.headers = DEFAULT_HEADERS.copy()
        self.session.headers.update(self.headers)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

    @staticmethod
    def _normalize_expected_status(expected_status: int | Iterable[int]) -> tuple[int, ...]:
        if isinstance(expected_status, int):
            return (expected_status,)
        return tuple(expected_status)

    def send_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        expected_status: int | Iterable[int] = 200,
        need_logging: bool = True,
    ) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=self.headers,
        )

        if need_logging:
            self.log_request_and_response(response)

        allowed_statuses = self._normalize_expected_status(expected_status)
        if response.status_code not in allowed_statuses:
            raise ValueError(
                f"Unexpected status code: {response.status_code}. "
                f"Expected one of: {allowed_statuses}. "
                f"Response body: {response.text}"
            )
        return response

    def _update_session_headers(self, **kwargs: str) -> None:
        self.headers.update(kwargs)
        self.session.headers.update(self.headers)

    def log_request_and_response(self, response: requests.Response) -> None:
        request = response.request
        try:
            response_payload = response.json()
        except ValueError:
            response_payload = response.text

        self.logger.info("REQUEST %s %s", request.method, request.url)
        self.logger.info("REQUEST HEADERS: %s", dict(request.headers))
        if request.body:
            self.logger.info("REQUEST BODY: %s", request.body)

        self.logger.info("RESPONSE STATUS: %s", response.status_code)
        self.logger.info(
            "RESPONSE BODY: %s",
            json.dumps(response_payload, ensure_ascii=False, indent=2)
            if isinstance(response_payload, (dict, list))
            else response_payload,
        )
