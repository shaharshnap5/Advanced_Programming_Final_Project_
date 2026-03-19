from __future__ import annotations

from fastapi import APIRouter
from src.db import get_db
from src.models.user import User
from src.services.rides_service import RideService


router = APIRouter(prefix="/rides", tags=["rides"])
service = RideService()


@router.get("/active-users", response_model=list[User])
async def get_active_users() -> list[User]:
    """Return all users who are currently in the middle of a ride."""
    async with get_db() as db:
        active_users = await service.list_active_users(db)
    return active_users
