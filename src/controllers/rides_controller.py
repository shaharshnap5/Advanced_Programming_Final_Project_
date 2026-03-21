from fastapi import APIRouter, HTTPException, Depends
import aiosqlite

from src.schemas.ride_schemas import RideStartRequest, EndRidePayload, EndRideResponse
from src.models.ride import Ride, User
from src.services.rides_service import RideService

# 3. Import your database connection dependency
from src.db import (
    get_db,
)  # Adjust this import based on where your get_db function lives

# Create the router
router = APIRouter(prefix="/rides", tags=["Rides"])

service = RideService()


@router.get("/active-users", response_model=list[User])
async def get_active_users(db: aiosqlite.Connection = Depends(get_db)) -> list[User]:
    """Return all users who are currently in the middle of a ride."""
    return await service.list_active_users(db)


@router.post("/start", response_model=Ride)  # Make sure this matches your return schema
async def start_ride(
    request: RideStartRequest, db: aiosqlite.Connection = Depends(get_db)
):
    try:
        # Pass the user_id, lon, and lat straight from the request into your service
        ride = await service.start_new_ride(
            db,
            user_id=request.user_id,
            lon=request.lon,
            lat=request.lat,
        )

        if not ride:
            raise HTTPException(status_code=404, detail="Could not start ride.")

        return ride

    except ValueError as e:
        # Catch any specific business logic errors you raise in the service
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        # Re-raise HTTPExceptions so their original status codes and details are preserved
        raise e
    except Exception as e:
        # Catch any unexpected crashes
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/end", response_model=EndRideResponse)
async def end_ride(payload: EndRidePayload, db: aiosqlite.Connection = Depends(get_db)):
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
    try:
        # Validate payload
        if not payload.ride_id or payload.lon is None or payload.lat is None:
            raise HTTPException(
                status_code=400, detail="Missing required fields: ride_id, lon, lat"
            )

        result = await service.end_ride(db, payload.ride_id, payload.lon, payload.lat)
        return result

    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
