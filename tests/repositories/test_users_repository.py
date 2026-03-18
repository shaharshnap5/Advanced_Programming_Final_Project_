from __future__ import annotations

import pytest

from src.models.user import User
from src.repositories.users_repository import UsersRepository


@pytest.mark.asyncio
async def test_create_and_get_user(test_db):
    repo = UsersRepository()

    created = await repo.create(test_db, "USER001", "tok_mock_123")
    assert created is True

    user = await repo.get_by_id(test_db, "USER001")
    assert user is not None
    assert isinstance(user, User)
    assert user.user_id == "USER001"
    assert user.payment_token == "tok_mock_123"
    assert user.current_ride_id is None


@pytest.mark.asyncio
async def test_create_existing_user_returns_false(test_db):
    repo = UsersRepository()

    created_first = await repo.create(test_db, "USER001", "tok_mock_123")
    assert created_first is True

    created_second = await repo.create(test_db, "USER001", "tok_other")
    assert created_second is False
