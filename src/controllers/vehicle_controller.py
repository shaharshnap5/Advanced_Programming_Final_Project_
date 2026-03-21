from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.db import get_db
from src.models.vehicle import Vehicle
from src.services.vehicles_service import VehiclesService


class VehicleTreatRequest(BaseModel):
    vehicle_id: str = Field(..., min_length=1)
    station_id: int | None = None


class VehicleReportRequest(BaseModel):
    vehicle_id: str = Field(..., min_length=1)


router = APIRouter(prefix="/vehicle", tags=["vehicle"])
service = VehiclesService()


@router.post("/treat", response_model=Vehicle)
async def treat_vehicle(request: VehicleTreatRequest) -> Vehicle:
    async with get_db() as db:
        treated_vehicle = await service.treat_vehicle(db, request.vehicle_id, request.station_id)
    return Vehicle.model_validate(treated_vehicle)


@router.post("/report-degraded", response_model=Vehicle)
async def report_vehicle_degraded(request: VehicleReportRequest) -> Vehicle:
    async with get_db() as db:
        updated_vehicle = await service.report_vehicle_degraded(db, request.vehicle_id)
    return Vehicle.model_validate(updated_vehicle)
