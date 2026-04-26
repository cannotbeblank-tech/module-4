from __future__ import annotations

from unittest.mock import Mock

import pytest
import requests
from pydantic import BaseModel

from custom_requester.custom_requester import CustomRequester


@pytest.mark.unit
class TestCustomRequester:
    def test_send_request_accepts_iterable_expected_statuses(self):
        session = requests.Session()
        requester = CustomRequester(session=session, base_url="https://example.com")
        response = Mock()
        response.status_code = 201
        response.text = '{"ok": true}'
        response.request = Mock(method="POST", url="https://example.com/resource", headers={}, body=None)
        session.request = Mock(return_value=response)
        requester.log_request_and_response = Mock()

        actual_response = requester._send_request(
            method="POST",
            endpoint="/resource",
            data={"name": "movie"},
            expected_status=(200, 201),
        )

        assert actual_response is response
        session.request.assert_called_once_with(
            method="POST",
            url="https://example.com/resource",
            json={"name": "movie"},
            params=None,
            headers=requester.headers,
        )

    def test_send_request_raises_for_unexpected_status(self):
        session = requests.Session()
        requester = CustomRequester(session=session, base_url="https://example.com")
        response = Mock()
        response.status_code = 500
        response.text = "boom"
        response.request = Mock(method="GET", url="https://example.com/resource", headers={}, body=None)
        session.request = Mock(return_value=response)
        requester.log_request_and_response = Mock()

        with pytest.raises(ValueError, match="Unexpected status code: 500"):
            requester._send_request(method="GET", endpoint="/resource", expected_status=200)

    def test_send_request_uses_error_model_for_non_2xx_status(self):
        class DummyErrorModel(BaseModel):
            message: str

        session = requests.Session()
        requester = CustomRequester(session=session, base_url="https://example.com")
        response = Mock()
        response.status_code = 400
        response.text = '{"message": "boom"}'
        response.json.return_value = {"message": "boom"}
        response.request = Mock(method="GET", url="https://example.com/resource", headers={}, body=None)
        session.request = Mock(return_value=response)
        requester.log_request_and_response = Mock()

        actual_response = requester._send_request(
            method="GET",
            endpoint="/resource",
            expected_status=(200, 400),
            success_model=Mock(),
            error_model=DummyErrorModel,
        )

        assert isinstance(actual_response, DummyErrorModel)
        assert actual_response.message == "boom"
