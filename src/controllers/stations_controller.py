from __future__ import annotations
from fastapi import Depends
import aiosqlite

from fastapi import APIRouter, Query

from src.db import get_db
from src.models.station import Station, StationWithDistance
from src.services.stations_service import StationsService
from src.exceptions import NotFoundException

router = APIRouter(prefix="/stations", tags=["stations"])
service = StationsService()


@router.get("/nearest", response_model=StationWithDistance)
async def get_nearest_station(
    lon: float = Query(..., description="Longitude"),
    lat: float = Query(..., description="Latitude"),
    db: aiosqlite.Connection = Depends(get_db)
) -> StationWithDistance:
    station = await service.get_nearest_station(db, lon=lon, lat=lat)

    if not station:
        raise NotFoundException("No stations found")

    return station


@router.get("/{station_id}", response_model=Station)
async def get_station(station_id: int,
                      db: aiosqlite.Connection = Depends(get_db)) -> Station:

    station = await service.get_station_by_id(db, station_id)

    if not station:
        raise NotFoundException("Station not found")

    return station
