from __future__ import annotations

from unittest.mock import Mock

import pytest
import requests

from api.auth_api import AuthAPI


@pytest.mark.unit
class TestAuthAPI:
    def test_authenticate_retries_on_transient_error_and_sets_bearer_token(self, monkeypatch: pytest.MonkeyPatch):
        auth_api = AuthAPI(requests.Session())
        fake_response = Mock()
        fake_response.json.return_value = {"accessToken": "token-123"}
        calls = {"count": 0}

        monkeypatch.setattr("api.auth_api.time.sleep", lambda *_args, **_kwargs: None)

        def fake_login_user(*args, **kwargs):
            calls["count"] += 1
            if calls["count"] < 3:
                raise ValueError("temporary auth failure")
            return fake_response

        monkeypatch.setattr(auth_api, "login_user", fake_login_user)
        result = auth_api.authenticate(("user@example.com", "password"))

        assert calls["count"] == 3
        assert result["accessToken"] == "token-123"
        assert auth_api.session.headers["Authorization"] == "Bearer token-123"

    def test_authenticate_raises_when_access_token_is_missing(self, monkeypatch: pytest.MonkeyPatch):
        auth_api = AuthAPI(requests.Session())
        fake_response = Mock()
        fake_response.json.return_value = {"refreshToken": "missing-access-token"}

        monkeypatch.setattr(auth_api, "login_user", lambda *args, **kwargs: fake_response)

        with pytest.raises(KeyError, match="accessToken is missing"):
            auth_api.authenticate(("user@example.com", "password"))
