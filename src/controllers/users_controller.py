from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import ValidationError
from aiosqlite import Connection

from src.db import get_db
from src.models.user import UserCreate, User
from src.services.users_service import UsersService

router = APIRouter(prefix="/users", tags=["users"])
service = UsersService()


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=User)
async def create_user(
    request: Request,
    db: Connection = Depends(get_db)
) -> User:
    """Register a new user and return the generated user_id."""
    try:
        payload = await request.json()
    except Exception:  # pragma: no cover
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        data = UserCreate.model_validate(payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())

    try:
        result = await service.create_user(
            db,
            data.user_id,
            data.first_name,
            data.last_name,
            data.email,
        )
    except ValueError as err:
        raise HTTPException(status_code=409, detail=str(err))

    return result
