import pytest
from httpx import AsyncClient, BasicAuth
import json

from app.core.config import settings
from app.models.user import User, UserRoles
from app.schemas.user import UserCreate


@pytest.mark.asyncio
class TestAuth:
    async def test_login(self, client: AsyncClient, super_user: User):
        login_data = {
            "username": super_user.username,
            "password": settings.FIRST_SUPERADMIN_PASSWORD,
        }
        # normal login
        response = await client.post(
            f"{settings.API_V1_STR}/auth/login", data=login_data
        )
        assert response.status_code == 200
        assert response.json().get("access_token")

        # invalid login
        response = await client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={"username": "invalid_user@gmail.com", "password": "invalid_pass"},
        )
        assert response.status_code == 404

    async def test_auth_and_tokens(
        self, client: AsyncClient, super_user_token: dict[str, str]
    ):
        response_me = await client.get(
            f"{settings.API_V1_STR}/auth/me", headers=super_user_token
        )
        assert response_me.status_code == 200
        assert "username" in response_me.json()["content"]

        # call service without tokens
        response = await client.get(f"{settings.API_V1_STR}/auth/me")
        assert response.status_code == 401

    async def test_basic_auth(self, client: AsyncClient):
        response = await client.get(
            f"{settings.API_V1_STR}/auth/me",
            auth=BasicAuth(
                settings.FIRST_SUPERADMIN, settings.FIRST_SUPERADMIN_PASSWORD
            ),
        )
        assert response.status_code == 200

        # invalid credentials
        response = await client.get(
            f"{settings.API_V1_STR}/auth/me",
            auth=BasicAuth("invalid_user", "invalid_pass"),
        )
        assert response.status_code == 401

    async def test_logout(self, client: AsyncClient, super_user_token: dict[str, str]):
        response = await client.get(
            f"{settings.API_V1_STR}/auth/logout", headers=super_user_token
        )
        assert response.status_code == 200

        # Verify token is no longer valid
        response_me = await client.get(
            f"{settings.API_V1_STR}/auth/me", headers=super_user_token
        )
        assert response_me.status_code == 401

    @property
    def register_data(self):
        self.username = "example@email.com"
        password = "password"

        return UserCreate(
            username=self.username, password=password, roles=[UserRoles.Consumer]
        ).model_dump()

    async def test_register(
        self, client: AsyncClient, super_user_token: dict[str, str]
    ):
        # normal register
        successful_response = await client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=self.register_data,
            headers=super_user_token,
        )

        assert successful_response.status_code == 200
        assert successful_response.json()["content"]["username"] == self.username

        # duplicate register
        unsuccessful_response = await client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=self.register_data,
            headers=super_user_token,
        )
        assert unsuccessful_response.status_code == 409
