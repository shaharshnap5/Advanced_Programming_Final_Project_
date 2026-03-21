from __future__ import annotations

import uuid
import aiosqlite

from src.models.user import User
from src.repositories.users_repository import UsersRepository


class UsersService:
    def __init__(self, repository: UsersRepository | None = None) -> None:
        self._repository = repository or UsersRepository()

    async def create_or_login_user(
        self,
        db: aiosqlite.Connection,
        user_id: str,
        first_name: str,
        last_name: str,
        email: str,
    ) -> tuple[User, bool]:
        """Register a new user or login existing user with provided user_id.

        If the user with the given user_id already exists, return their data.
        If the user does not exist, create a new account with a mocked payment token.

        Args:
            db: Database connection
            user_id: Unique user identifier provided by the client
            first_name: User's first name
            last_name: User's last name
            email: User's email address

        Returns:
            tuple[User, bool]: A tuple of (User object, is_existing_user)
                - User: The created or existing user model with mocked payment token
                - is_existing_user: True if user already existed, False if newly created
        """
        # Check if user already exists
        existing_user = await self._repository.get_by_id(db, user_id)
        if existing_user:
            return existing_user, True

        # User does not exist, create new account
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
            raise ValueError(f"Failed to create user with id {user_id}")

        return User(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            payment_token=token,
        ), False
