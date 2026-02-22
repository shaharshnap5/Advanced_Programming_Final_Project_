from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from src.db import get_db
from src.models.station import Station, StationWithDistance
from src.services.stations_service import StationsService

router = APIRouter(prefix="/stations", tags=["stations"])
service = StationsService()


@router.get("/nearest", response_model=StationWithDistance)
async def get_nearest_station(
    lon: float = Query(..., description="Longitude"),
    lat: float = Query(..., description="Latitude"),
) -> StationWithDistance:
    async with get_db() as db:
        station = await service.get_nearest_station(db, lon=lon, lat=lat)

    if not station:
        raise HTTPException(status_code=404, detail="No stations found")

    return StationWithDistance.model_validate(station)


@router.get("/{station_id}", response_model=Station)
async def get_station(station_id: int) -> Station:
    async with get_db() as db:
        station = await service.get_station_by_id(db, station_id)

    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    return Station.model_validate(station)
