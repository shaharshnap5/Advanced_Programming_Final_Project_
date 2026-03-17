from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ValidationError, Field
from aiosqlite import Connection

from src.db import get_db
from src.services.users_service import UsersService
from src.models.user import User


class UserCreate(BaseModel):
    user_id: str = Field(..., min_length=1, description="Unique identifier for the user")


router = APIRouter(prefix="/users", tags=["users"])
service = UsersService()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=User)
async def create_user(request: Request, db: Connection = Depends(get_db)) -> User:
    """Register a new user and return the created user model."""
    try:
        payload = await request.json()
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        data = UserCreate.model_validate(payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())

    try:
        result = await service.create_user(db, data.user_id)
    except ValueError as err:
        raise HTTPException(status_code=409, detail=str(err))

    return result
