from __future__ import annotations

from fastapi import APIRouter
from src.db import get_db
from src.schemas.ride_schemas import ActiveUsersResponse
from src.services.rides_service import RideService


router = APIRouter(prefix="/rides", tags=["rides"])
service = RideService()


@router.get("/active-users", response_model=ActiveUsersResponse)
async def get_active_users() -> ActiveUsersResponse:
    """Return all users who are currently in the middle of a ride."""
    async with get_db() as db:
        active_user_ids = await service.list_active_user_ids(db)
    return ActiveUsersResponse(active_user_ids=active_user_ids)
