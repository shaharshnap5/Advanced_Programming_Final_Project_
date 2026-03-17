from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException, Request, status
from pydantic import BaseModel, ValidationError

from src.db import get_db
from src.services.rides_service import RidesService


class EndRidePayload(BaseModel):
    ride_id: str
    lon: float
    lat: float


router = APIRouter(prefix="/ride", tags=["rides"])
service = RidesService()


@router.post("/end")
async def end_ride(request: Request) -> dict:
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        data = EndRidePayload.model_validate(payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())

    async with get_db() as db:
        return await service.end_ride(db, data.ride_id, data.lon, data.lat)
