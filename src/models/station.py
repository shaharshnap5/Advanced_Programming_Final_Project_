from __future__ import annotations

from pydantic import BaseModel


class Station(BaseModel):
    station_id: int
    name: str
    lat: float
    lon: float
    max_capacity: int


class StationWithDistance(Station):
    distance: float
