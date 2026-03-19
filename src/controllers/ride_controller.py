from fastapi import APIRouter, Depends
import aiosqlite

from src.schemas.ride_schemas import RideStartRequest
from src.models.ride import Ride
from src.services.rides_service import RideService
from src.db import get_db

router = APIRouter(prefix="/ride", tags=["Rides"])

service = RideService()


@router.post("/start", response_model=Ride)
async def start_ride(
    request: RideStartRequest,
    db: aiosqlite.Connection = Depends(get_db)
) -> Ride:
    """Start a new ride for a user at a given location."""
    ride = await service.start_new_ride(
        db,
        user_id=request.user_id,
        lon=request.lon,
        lat=request.lat
    )
    return ride