from __future__ import annotations

import uuid
import aiosqlite

from src.models.user import User
from src.repositories.users_repository import UsersRepository


class UsersService:
    def __init__(self, repository: UsersRepository | None = None) -> None:
        self._repository = repository or UsersRepository()

    async def create_user(self, db: aiosqlite.Connection, user_id: str) -> User:
        """Create a new user with a mocked payment token.

        Raises:
            ValueError: if the user already exists.
        """
        existing = await self._repository.get_by_id(db, user_id)
        if existing:
            raise ValueError("User already exists")

        # Mocked billing token
        token = uuid.uuid4().hex

        created = await self._repository.create(db, user_id=user_id, payment_token=token)
        if not created:
            raise Exception("Failed to create user")

        return User(user_id=user_id, payment_token=token)
