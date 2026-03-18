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
            mock_create_user.return_value = User(user_id="USER001", payment_token="tok")

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/users/register", json={"user_id": "USER001"})

            assert response.status_code == 201
            assert response.json()["user_id"] == "USER001"


@pytest.mark.asyncio
async def test_create_user_conflict():
    with patch("src.controllers.users_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db

        with patch("src.controllers.users_controller.service.create_user") as mock_create_user:
            mock_create_user.side_effect = ValueError("User already exists")

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/users/register", json={"user_id": "USER001"})

            assert response.status_code == 409
            assert response.json()["detail"] == "User already exists"


@pytest.mark.asyncio
async def test_create_user_invalid_payload():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/users/register", json={})

    assert response.status_code == 400
    assert "user_id" in response.json()["detail"][0]["loc"]
