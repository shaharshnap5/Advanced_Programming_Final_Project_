from __future__ import annotations
from pydantic import BaseModel
import datetime
from abc import ABC, abstractmethod



class Vehicle(BaseModel, ABC):
    vehicle_id: str
    station_id: int | None
    vehicle_type: str
    status: str
    rides_since_last_treated: int
    last_treated_date: datetime.date | None

    @abstractmethod
    def rent(self):
        pass


    def return_vehicle(self, station_id: int):
        """Returns the vehicle to a station and updates its status."""

        self.station_id = station_id
        if self.rides_since_last_treated >= 7:
            self.status = 'degraded'
        else:
            self.status = 'available'

    def report_degraded(self):
        self.status = 'degraded'


    @abstractmethod
    def treat(self, treatment_date: str):
       pass



class ElectricVehicle(Vehicle, ABC):
    battery_level: int

    def treat(self):
        """Treats the electric vehicle by resetting its status, rides count, last treated date, and recharging the battery."""

        self.status = 'available'
        self.rides_since_last_treated = 0
        self.last_treated_date = datetime.date.today()
        self.battery_level = 100 # Recharge battery during treatment


    def rent(self):
        """Rents the electric vehicle if it's available and has sufficient battery."""

        if self.status == 'available' and self.rides_since_last_treated < 7 and self.battery_level > 20: # Check battery level before renting
            self.status = 'rented'
            self.station_id = None
        else:
            raise Exception("Electric vehicle is not available for rent")

    def charge(self):
        """Charges the electric vehicle's battery to full if it's available."""

        if self.status == 'available':
            self.battery_level = 100
        else:
            raise Exception("Cannot charge a vehicle that is not available")



class Bicycle(Vehicle):
    vehicle_type: str = 'bike'

    def rent(self):
        """Rents the bicycle if it's available and has not reached the treatment threshold."""

        if self.status == 'available' and self.rides_since_last_treated < 7:
            self.status = 'rented'
            self.station_id = None
        else:
            raise Exception("Bike is not available for rent")

    def treat(self):
        """Treats the bicycle by resetting its status, rides count, and last treated date."""

        self.status = 'available'
        self.rides_since_last_treated = 0
        self.last_treated_date = datetime.date.today()


class ElectricBicycle(ElectricVehicle):
    vehicle_type: str = 'ebike'
    battery_level: int = 100

    # The rent and treat methods are inherited from ElectricVehicle, \n
    # so we don't need to implement them here unless we want to add specific behavior for electric bicycles.



class Scooter(ElectricVehicle):
    vehicle_type: str = 'scooter'
    battery_level: int = 100

    # The rent and treat methods are inherited from ElectricVehicle, \n
    # so we don't need to implement them here unless we want to add specific behavior for electric bicycles.


class VehicleFactory:
    @staticmethod
    def create_vehicle(vehicle_id: str, vehicle_type: str, station_id: int | None = None) -> Vehicle:
        base_data = {
            "vehicle_id": vehicle_id,
            "station_id": station_id,
            "status": "available",
            "rides_since_last_treated": 0,
            "last_treated_date": None
        }

        v_type = {
            "bike": Bicycle(vehicle_type="bike", **base_data),
            "ebike": ElectricBicycle(vehicle_type="ebike", **base_data),
            "scooter": Scooter(vehicle_type="scooter", **base_data)
        }
        return v_type[vehicle_type.lower()]


