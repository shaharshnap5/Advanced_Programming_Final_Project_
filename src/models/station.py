from __future__ import annotations

from pydantic import BaseModel
import math

def calculate_euclidean_distance(lat1: float, lon1: float, lat2: float, lon2: float):
    """
    Calculate the Euclidean distance between two geographic points.
    """
    return math.sqrt((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2)



class Station(BaseModel):
    station_id: int
    name: str
    lat: float
    lon: float
    max_capacity: int


class StationWithDistance(Station):
    distance: float

