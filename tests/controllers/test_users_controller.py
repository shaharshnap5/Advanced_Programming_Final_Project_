from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from src.models.user import User
from src.main import app


@pytest.mark.asyncio
async def test_create_user_success():
    with patch("src.controllers.users_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.users_controller.service.create_user") as mock_create_user:
            mock_create_user.return_value = User(
                user_id="USER001",
                first_name="Test",
                last_name="User",
                email="test@example.com",
                payment_token="tok",
            )

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/users/register",
                    json={
                        "first_name": "Test",
                        "last_name": "User",
                        "email": "test@example.com",
                    },
                )

            assert response.status_code == 201
            assert response.json()["user_id"] == "USER001"
            assert response.json()["first_name"] == "Test"
            assert response.json()["last_name"] == "User"
            assert response.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_create_user_conflict():
    with patch("src.controllers.users_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.users_controller.service.create_user") as mock_create_user:
            mock_create_user.side_effect = ValueError("User already exists")

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/users/register",
                    json={
                        "first_name": "Test",
                        "last_name": "User",
                        "email": "test@example.com",
                    },
                )

            assert response.status_code == 409
            assert response.json()["detail"] == "User already exists"


@pytest.mark.asyncio
async def test_create_user_invalid_payload():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/users/register", json={})

    assert response.status_code == 400
    missing_fields = {error["loc"][-1] for error in response.json()["detail"]}
    assert {"first_name", "last_name", "email"}.issubset(missing_fields)


@pytest.mark.asyncio
async def test_get_active_users_success():
    with patch("src.controllers.users_controller.service.list_active_users", new_callable=AsyncMock) as mock_active:
        mock_active.return_value = [
            User(user_id="USER_A", first_name="A", last_name="A", email="a@example.com", payment_token="tok1"),
            User(user_id="USER_B", first_name="B", last_name="B", email="b@example.com", payment_token="tok2"),
        ]

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/users/active")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 2
        assert response.json()[0]["user_id"] == "USER_A"
        assert response.json()[1]["user_id"] == "USER_B"


@pytest.mark.asyncio
async def test_get_active_users_empty_list():
    with patch("src.controllers.users_controller.service.list_active_users", new_callable=AsyncMock) as mock_active:
        mock_active.return_value = []

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/users/active")

        assert response.status_code == 200
        assert response.json() == []
