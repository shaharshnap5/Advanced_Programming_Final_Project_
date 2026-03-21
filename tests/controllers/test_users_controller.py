from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from src.models.user import User
from src.main import app


@pytest.mark.asyncio
async def test_create_user_success():
    """Test successful creation of a new user."""
    with patch("src.controllers.users_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch(
            "src.controllers.users_controller.service.create_or_login_user"
        ) as mock_create_or_login:
            user = User(
                user_id="user123",
                first_name="Test",
                last_name="User",
                email="test@example.com",
                payment_token="tok",
            )
            mock_create_or_login.return_value = (user, False)  # New user

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/users/register",
                    json={
                        "user_id": "user123",
                        "first_name": "Test",
                        "last_name": "User",
                        "email": "test@example.com",
                    },
                )

            assert response.status_code == 201
            assert response.json()["message"] == "User created successfully"
            assert response.json()["user"]["user_id"] == "user123"
            assert response.json()["user"]["first_name"] == "Test"
            assert response.json()["user"]["last_name"] == "User"
            assert response.json()["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_login_existing_user():
    """Test login of an existing user with same user_id."""
    with patch("src.controllers.users_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch(
            "src.controllers.users_controller.service.create_or_login_user"
        ) as mock_create_or_login:
            user = User(
                user_id="user123",
                first_name="Test",
                last_name="User",
                email="test@example.com",
                payment_token="tok_existing",
            )
            mock_create_or_login.return_value = (user, True)  # Existing user

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/users/register",
                    json={
                        "user_id": "user123",
                        "first_name": "Test",
                        "last_name": "User",
                        "email": "test@example.com",
                    },
                )

            assert response.status_code == 200
            assert response.json()["message"] == "User already exists, details:"
            assert response.json()["user"]["user_id"] == "user123"
            assert response.json()["user"]["payment_token"] == "tok_existing"


@pytest.mark.asyncio
async def test_create_user_conflict():
    """Test error handling when user creation fails."""
    with patch("src.controllers.users_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch(
            "src.controllers.users_controller.service.create_or_login_user"
        ) as mock_create_or_login:
            mock_create_or_login.side_effect = ValueError(
                "Failed to create user with id user123"
            )

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/users/register",
                    json={
                        "user_id": "user123",
                        "first_name": "Test",
                        "last_name": "User",
                        "email": "test@example.com",
                    },
                )

            assert response.status_code == 409
            assert "Failed to create user" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_user_invalid_payload():
    """Test validation of required fields."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/users/register", json={})

    assert response.status_code == 400
    missing_fields = {error["loc"][-1] for error in response.json()["detail"]}
    assert {"user_id", "first_name", "last_name", "email"}.issubset(missing_fields)


@pytest.mark.asyncio
async def test_create_user_missing_user_id():
    """Test validation when user_id is missing."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/users/register",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
            },
        )

    assert response.status_code == 400
    missing_fields = {error["loc"][-1] for error in response.json()["detail"]}
    assert "user_id" in missing_fields
