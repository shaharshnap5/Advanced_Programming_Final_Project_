from __future__ import annotations

import uuid
import aiosqlite

from src.repositories.users_repository import UsersRepository


class UsersService:
    def __init__(self, repository: UsersRepository | None = None) -> None:
        self._repository = repository or UsersRepository()

    async def create_user(self, db: aiosqlite.Connection, user_id: str) -> dict:
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

        return {"user_id": user_id, "payment_token": token}

    async def get_user_by_id(self, db: aiosqlite.Connection, user_id: str) -> dict | None:
        return await self._repository.get_by_id(db, user_id)

    async def clear_current_ride(self, db: aiosqlite.Connection, user_id: str) -> bool:
        return await self._repository.update_current_ride_id(db, user_id, None)

    async def list_active_users(self, db: aiosqlite.Connection) -> list[dict]:
        return await self._repository.list_active_users(db)
