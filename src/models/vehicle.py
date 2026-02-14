from __future__ import annotations

from pydantic import BaseModel


class Vehicle(BaseModel):
    vehicle_id: str
    station_id: int | None
    vehicle_type: str
    status: str
    rides_since_last_treated: int
    last_treated_date: str | None
