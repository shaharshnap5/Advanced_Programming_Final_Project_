from __future__ import annotations

from fastapi import APIRouter, Depends, status
from aiosqlite import Connection

from src.db import get_db
from src.models.user import UserCreate, User
from src.services.users_service import UsersService

router = APIRouter(prefix="/users", tags=["users"])
service = UsersService()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: Connection = Depends(get_db)
) -> User:
    """Register a new user and return the created user."""
    result = await service.create_user(
        db,
        data.user_id,
        data.first_name,
        data.last_name,
        data.email,
    )
    return result
