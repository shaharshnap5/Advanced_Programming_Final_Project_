from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch

from src.models.user import User
from src.services.users_service import UsersService
from src.repositories.users_repository import UsersRepository


@pytest.mark.asyncio
async def test_create_user_success():
    mock_repo = Mock(spec=UsersRepository)
    mock_repo.get_by_id = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock(return_value=True)

    service = UsersService(repository=mock_repo)
    mock_db = Mock()

    with patch("src.services.users_service.uuid.uuid4") as mock_uuid4:
        mock_uuid4.return_value = Mock(hex="mocked_token")
        result = await service.create_user(mock_db, "USER001", "Test", "User", "test@example.com")

    assert isinstance(result, User)
    assert result.user_id == "USER001"
    assert result.first_name == "Test"
    assert result.last_name == "User"
    assert result.email == "test@example.com"
    assert result.payment_token == "mocked_token"
    mock_repo.get_by_id.assert_called_once_with(mock_db, "USER001")
    mock_repo.create.assert_called_once_with(
        mock_db,
        user_id="USER001",
        first_name="Test",
        last_name="User",
        email="test@example.com",
        payment_token="mocked_token",
    )


@pytest.mark.asyncio
async def test_create_user_conflict():
    mock_repo = Mock(spec=UsersRepository)
    mock_repo.get_by_id = AsyncMock(
        return_value=User(
            user_id="USER001",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            payment_token="mocked_token",
        )
    )

    service = UsersService(repository=mock_repo)
    mock_db = Mock()

    with pytest.raises(ValueError, match="User already exists"):
        await service.create_user(mock_db, "USER001", "Test", "User", "test@example.com")
