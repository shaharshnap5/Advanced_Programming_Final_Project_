from __future__ import annotations

import uuid
import aiosqlite

from src.models.user import User
from src.repositories.users_repository import UsersRepository


class UsersService:
    def __init__(self, repository: UsersRepository | None = None) -> None:
        self._repository = repository or UsersRepository()

    async def _generate_unique_user_id(self, db: aiosqlite.Connection) -> str:
        """Generate a unique server-side user identifier."""

        for _ in range(10):
            candidate = str(uuid.uuid4())
            existing = await self._repository.get_by_id(db, candidate)
            if not existing:
                return candidate

        raise ValueError("Failed to generate unique user id")

    async def create_user(
        self,
        db: aiosqlite.Connection,
        first_name: str,
        last_name: str,
        email: str,
    ) -> User:
        """Create a new user with a mocked payment token.

        Returns:
            User: The created user model

        Raises:
            ValueError: if user id generation fails.
        """
        user_id = await self._generate_unique_user_id(db)

        # Mocked billing token
        token = uuid.uuid4().hex

        created = await self._repository.create(
            db,
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            payment_token=token,
        )
        if not created:
            raise Exception("Failed to create user")

        return User(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            payment_token=token,
        )
