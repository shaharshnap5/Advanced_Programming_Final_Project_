from __future__ import annotations

import pytest
import uuid
from unittest.mock import AsyncMock, Mock, patch

from src.models.user import User
from src.services.users_service import UsersService
from src.repositories.users_repository import UsersRepository


@pytest.mark.asyncio
async def test_create_user_success():
    """Test successful creation of a new user when user_id doesn't exist."""
    mock_repo = Mock(spec=UsersRepository)
    mock_repo.get_by_id = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock(return_value=True)

    service = UsersService(repository=mock_repo)
    mock_db = Mock()

    with patch("src.services.users_service.uuid.uuid4") as mock_uuid4:
        mock_uuid4.return_value = Mock(hex="mocked_token")
        result, is_existing = await service.create_or_login_user(
            mock_db, "user123", "Test", "User", "test@example.com"
        )

    assert isinstance(result, User)
    assert result.user_id == "user123"
    assert result.first_name == "Test"
    assert result.last_name == "User"
    assert result.email == "test@example.com"
    assert result.payment_token == "mocked_token"
    assert is_existing is False  # New user should return False

    mock_repo.get_by_id.assert_called_once_with(mock_db, "user123")
    mock_repo.create.assert_called_once_with(
        mock_db,
        user_id="user123",
        first_name="Test",
        last_name="User",
        email="test@example.com",
        payment_token="mocked_token",
    )


@pytest.mark.asyncio
async def test_login_existing_user():
    """Test login of an existing user - returns user without creating new one."""
    existing_user = User(
        user_id="user123",
        first_name="Test",
        last_name="User",
        email="test@example.com",
        payment_token="existing_token",
    )
    mock_repo = Mock(spec=UsersRepository)
    mock_repo.get_by_id = AsyncMock(return_value=existing_user)
    mock_repo.create = AsyncMock(return_value=True)

    service = UsersService(repository=mock_repo)
    mock_db = Mock()

    result, is_existing = await service.create_or_login_user(
        mock_db, "user123", "Test", "User", "test@example.com"
    )

    assert isinstance(result, User)
    assert result.user_id == "user123"
    assert result.payment_token == "existing_token"
    assert is_existing is True  # Existing user should return True

    mock_repo.get_by_id.assert_called_once_with(mock_db, "user123")
    # create should not be called when user already exists
    mock_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_user_failure():
    """Test failure when repository fails to create user."""
    mock_repo = Mock(spec=UsersRepository)
    mock_repo.get_by_id = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock(return_value=False)

    service = UsersService(repository=mock_repo)
    mock_db = Mock()

    with patch("src.services.users_service.uuid.uuid4") as mock_uuid4:
        mock_uuid4.return_value = Mock(hex="mocked_token")
        with pytest.raises(ValueError, match="Failed to create user with id user123"):
            await service.create_or_login_user(
                mock_db, "user123", "Test", "User", "test@example.com"
            )
