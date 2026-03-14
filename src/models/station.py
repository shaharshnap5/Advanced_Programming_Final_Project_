from __future__ import annotations

from pydantic import BaseModel, Field
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
    vehicles: list[str]  = Field(default_factory=list) # List of vehicle IDs currently at the station


    def has_available_vehicle(self):
        """Checks if there is at least one vehicle available at the station."""

        return self.vehicles is not None and len(self.vehicles) > 0


    def has_free_spot(self):
        """Checks if there is at least one free spot available at the station."""

        return self.vehicles is None or len(self.vehicles) < self.max_capacity


    def add_vehicle(self, vehicle_id: str):
        """Adds a vehicle to the station if there is capacity."""

        if self.vehicles is None:
            self.vehicles = []
        if len(self.vehicles) < self.max_capacity:
            self.vehicles.append(vehicle_id)
        else:
            raise Exception("Station is at full capacity")


    def remove_vehicle(self, vehicle_id: str):
        """Removes a vehicle from the station if it exists."""

        if self.vehicles is not None and vehicle_id in self.vehicles:
            self.vehicles.remove(vehicle_id)
        else:
            raise Exception("Vehicle not found at this station")



class StationWithDistance(Station):
    distance: float

