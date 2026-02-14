from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from src.db import get_db
from src.models.vehicle import Vehicle
from src.services.vehicles_service import VehiclesService

router = APIRouter(prefix="/vehicles", tags=["vehicles"])
service = VehiclesService()


@router.get("/{vehicle_id}", response_model=Vehicle)
async def get_vehicle(vehicle_id: str) -> Vehicle:
    async with get_db() as db:
        vehicle = await service.get_vehicle_by_id(db, vehicle_id)

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    return Vehicle.model_validate(vehicle)


@router.get("", response_model=list[Vehicle])
async def list_vehicles(
    station_id: int | None = Query(None, description="Filter by station_id"),
) -> list[Vehicle]:
    async with get_db() as db:
        if station_id is None:
            vehicles = await service.list_vehicles(db)
        else:
            vehicles = await service.list_vehicles_by_station(db, station_id)

    return [Vehicle.model_validate(v) for v in vehicles]
