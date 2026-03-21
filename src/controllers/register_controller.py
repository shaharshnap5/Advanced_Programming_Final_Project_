from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.db import get_db
from src.services.users_service import UsersService


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1)
    credit_token: str = Field(..., min_length=1)


router = APIRouter(tags=["register"])
service = UsersService()


@router.post("/register")
async def register(request: RegisterRequest) -> dict[str, str]:
    async with get_db() as db:
        return await service.register_user(db, request.name, request.credit_token)
