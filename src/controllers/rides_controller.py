from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.db import get_db
from src.services.rides_service import RidesService


class RideStartRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    lat: float
    lon: float


class RideEndRequest(BaseModel):
    ride_id: str = Field(..., min_length=1)
    lat: float
    lon: float


router = APIRouter(tags=["rides"])
service = RidesService()


@router.post("/ride/start")
async def start_ride(request: RideStartRequest) -> dict:
    async with get_db() as db:
        return await service.start_ride(db, request.user_id, request.lat, request.lon)


@router.post("/ride/end")
async def end_ride(request: RideEndRequest) -> dict:
    async with get_db() as db:
        return await service.end_ride(db, request.ride_id, request.lat, request.lon)


@router.get("/rides/active-users")
async def get_active_users() -> dict[str, list[str]]:
    async with get_db() as db:
        users = await service.get_active_users(db)
    return {"active_users": users}
