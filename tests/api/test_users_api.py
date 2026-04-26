from __future__ import annotations

import allure
import pytest

from api.api_manager import ApiManager


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.regression
@allure.epic("Cinescope")
@allure.feature("Users API")
class TestUsersAPI:
    @allure.story("Role model")
    @allure.title("USER cannot read /user/{idOrEmail}")
    def test_user_cannot_get_user_by_locator(
        self,
        common_user_api_manager: ApiManager,
    ):
        response = common_user_api_manager.user_api.get_user(
            common_user_api_manager.user_email,
            expected_status=403,
        )

        assert response.message == "Forbidden resource"

    @pytest.mark.parametrize(
        "actor_fixture",
        ["admin_api_manager", "super_admin_api_manager"],
        ids=["admin-allowed", "super-admin-allowed"],
    )
    @allure.story("Role model")
    @allure.title("ADMIN-like roles can read /user/{idOrEmail}")
    def test_admin_roles_can_get_user_by_locator(
        self,
        request: pytest.FixtureRequest,
        actor_fixture: str,
    ):
        actor: ApiManager = request.getfixturevalue(actor_fixture)

        response = actor.user_api.get_user(actor.user_email)

        assert response.email == actor.user_email
        assert response.roles == actor.user_roles
        assert response.verified is True
