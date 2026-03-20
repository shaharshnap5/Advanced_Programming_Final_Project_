from __future__ import annotations
from fastapi import Depends
import aiosqlite
from fastapi import APIRouter, HTTPException, Query

from src.db import get_db
from src.models.vehicle import Vehicle
from src.services.vehicles_service import VehiclesService

router = APIRouter(prefix="/vehicles", tags=["vehicles"])
service = VehiclesService()


@router.get("/{vehicle_id}", response_model=Vehicle)
async def get_vehicle(vehicle_id: str,
                      db: aiosqlite.Connection = Depends(get_db)) -> Vehicle:
    vehicle = await service.get_vehicle_by_id(db, vehicle_id)

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    return vehicle


@router.post("/{vehicle_id}/treat", response_model=Vehicle)
async def treat_vehicle(
    vehicle_id: str,
    station_id: int | None = Query(None, description="Station to assign (required for degraded vehicles without station)"),
    db: aiosqlite.Connection = Depends(get_db)
) -> Vehicle:
    """Perform maintenance on a vehicle.
    Requirements:
    - Vehicle must be degraded OR have >= 7 rides since last treatment
    - Sets status='available', rides_since_last_treated=0, last_treated_date=today
    - Assigns station for previously degraded vehicles
    """
    try:
        treated_vehicle = await service.treat_vehicle(db, vehicle_id, station_id)
        return treated_vehicle
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{vehicle_id}/report-degraded", response_model=Vehicle)
async def report_degraded(vehicle_id: str,
                            db: aiosqlite.Connection = Depends(get_db)
                          ) -> Vehicle:
    """Endpoint for users to report a vehicle as degraded. Marks it degraded regardless of ride count."""
    try:
        updated = await service.report_vehicle_degraded(db, vehicle_id)
        return updated
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        elif "already marked as degraded" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
