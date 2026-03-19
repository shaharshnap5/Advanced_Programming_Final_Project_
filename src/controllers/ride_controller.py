from fastapi import APIRouter, Depends
import aiosqlite

from src.schemas.ride_schemas import RideStartRequest, EndRidePayload
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


@router.post("/end")
async def end_ride(
    payload: EndRidePayload,
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    End an active ride and dock the vehicle at the nearest station with available capacity.

    Request body:
    - ride_id: str - The unique identifier of the ride to end
    - lon: float - The longitude of the drop-off location
    - lat: float - The latitude of the drop-off location

    Returns:
    - end_station_id: int - The ID of the station where vehicle was docked
    - payment_charged: int - The amount charged (15 ILS for normal ride, 0 for degraded)
    """
    result = await service.end_ride(db, payload.ride_id, payload.lon, payload.lat)
    return result