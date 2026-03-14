from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ValidationError, Field

from src.db import get_db
from src.services.users_service import UsersService


class UserCreate(BaseModel):
    user_id: str = Field(..., min_length=1, description="Unique identifier for the user")


router = APIRouter(prefix="/users", tags=["users"])
service = UsersService()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(request: Request) -> dict[str, str]:
    """Register a new user and return the generated user_id."""
    try:
        payload = await request.json()
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        data = UserCreate.model_validate(payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())

    async with get_db() as db:
        try:
            result = await service.create_user(db, data.user_id)
        except ValueError as err:
            raise HTTPException(status_code=409, detail=str(err))

    return {"user_id": result["user_id"]}
