from __future__ import annotations

import allure
import pytest

from api.api_manager import ApiManager


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.flaky(reruns=2, reruns_delay=1)
@pytest.mark.regression
@allure.epic("Cinescope")
@allure.feature("Users API")
class TestUsersAPI:
    @pytest.mark.parametrize(
        ("actor_fixture", "expected_status"),
        [
            ("common_user_api_manager", 403),
            ("admin_api_manager", 200),
            ("super_admin_api_manager", 200),
        ],
        ids=["user-forbidden", "admin-allowed", "super-admin-allowed"],
    )
    @allure.story("Role model")
    @allure.title("GET /user/{{idOrEmail}} respects role permissions for {actor_fixture}")
    def test_get_user_by_locator_respects_role_permissions(
        self,
        request: pytest.FixtureRequest,
        actor_fixture: str,
        expected_status: int,
    ):
        actor: ApiManager = request.getfixturevalue(actor_fixture)

        with allure.step(f"Request user profile as {actor_fixture}"):
            response = actor.user_api.get_user(actor.user_email, expected_status=expected_status)

        with allure.step("Validate role-based access to GET /user/{idOrEmail}"):
            if expected_status == 403:
                payload = response.json()
                assert payload["message"] == "Forbidden resource"
            else:
                payload = response.json()
                assert payload["email"] == actor.user_email
                assert payload["roles"] == actor.user_roles
                assert payload["verified"] is True
