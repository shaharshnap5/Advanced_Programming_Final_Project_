from fastapi import APIRouter, HTTPException, Depends
import aiosqlite

from src.schemas.ride_schemas import RideStartRequest
from src.models.ride import Ride
from src.services.rides_service import RideService

# 3. Import your database connection dependency
from src.db import get_db  # Adjust this import based on where your get_db function lives

# Create the router
router = APIRouter(prefix="/ride", tags=["Rides"])

service = RideService()

@router.post("/start", response_model=Ride)  # Make sure this matches your return schema
async def start_ride(
        request: RideStartRequest,
        db: aiosqlite.Connection = Depends(get_db)
):
    try:
        # Pass the user_id, lon, and lat straight from the request into your service
        ride = await service.start_new_ride(
            db,
            user_id=request.user_id,
            lon=request.lon,
            lat=request.lat
        )

        if not ride:
            raise HTTPException(status_code=404, detail="Could not start ride.")

        return ride

    except ValueError as e:
        # Catch any specific business logic errors you raise in the service
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch any unexpected crashes
        raise HTTPException(status_code=500, detail=str(e))