from __future__ import annotations
from pydantic import BaseModel
import datetime
from enum import Enum

class VehicleType(str, Enum):
    bike = 'bike'
    ebike = 'ebike'
    scooter = 'scooter'

class VehicleStatus(str, Enum):
    available = 'available'
    rented = 'rented'
    degraded = 'degraded'


class Vehicle(BaseModel):
    vehicle_id: str
    station_id: int | None
    vehicle_type: VehicleType
    status: VehicleStatus
    rides_since_last_treated: int
    last_treated_date: datetime.date | None

    def rent(self):
        """Base rent method. Override in subclasses for specific behavior."""
        pass


    def return_vehicle(self, station_id: int):
        """Returns the vehicle to a station and updates its status.

        Degradation occurs only after more than 10 rides since last treatment.
        """

        self.station_id = station_id
        if self.rides_since_last_treated > 10:
            # once the ride count exceeds 10, vehicle becomes degraded
            self.status = VehicleStatus.degraded
        else:
            self.status = VehicleStatus.available

    def report_degraded(self):
        self.status = VehicleStatus.degraded


    def treat(self):
        """Base treat method. Override in subclasses for specific behavior."""
        pass



class ElectricVehicle(Vehicle):
    battery_level: int

    def treat(self):
        """Treats the electric vehicle by resetting its status, rides count, last treated date, and recharging the battery."""

        self.status = VehicleStatus.available
        self.rides_since_last_treated = 0
        self.last_treated_date = datetime.date.today()
        self.battery_level = 100 # Recharge battery during treatment


    def rent(self):
        """Rents the electric vehicle if it's available, within ride threshold, and has sufficient battery."""

        # eligibility: must be available, <=10 rides since last treatment, battery >20%
        if self.status == VehicleStatus.available and self.rides_since_last_treated <= 10 and self.battery_level > 20:
            self.status = VehicleStatus.rented
            self.station_id = None
        else:
            raise Exception("Electric vehicle is not available for rent")

    def charge(self):
        """Charges the electric vehicle's battery to full if it's available."""

        if self.status == VehicleStatus.available:
            self.battery_level = 100
        else:
            raise Exception("Cannot charge a vehicle that is not available")



class Bicycle(Vehicle):
    vehicle_type: VehicleType = VehicleType.bike

    def rent(self):
        """Rents the bicycle if it's available and within the eligibility rules."""

        # a bike can be rented only when status is available and rides_since_last_treated <= 10
        if self.status == VehicleStatus.available and self.rides_since_last_treated <= 10:
            self.status = VehicleStatus.rented
            self.station_id = None
        else:
            raise Exception("Bike is not available for rent")

    def treat(self):
        """Treats the bicycle by resetting its status, rides count, and last treated date."""

        self.status = VehicleStatus.available
        self.rides_since_last_treated = 0
        self.last_treated_date = datetime.date.today()


class ElectricBicycle(ElectricVehicle):
    vehicle_type: VehicleType = VehicleType.ebike
    battery_level: int = 100

    # The rent and treat methods are inherited from ElectricVehicle, \n
    # so we don't need to implement them here unless we want to add specific behavior for electric bicycles.



class Scooter(ElectricVehicle):
    vehicle_type: VehicleType = VehicleType.scooter
    battery_level: int = 100

    # The rent and treat methods are inherited from ElectricVehicle, \n
    # so we don't need to implement them here unless we want to add specific behavior for electric bicycles.


class VehicleFactory:
    @staticmethod
    def create_vehicle(vehicle_id: str, vehicle_type: str, station_id: int | None = None) -> Vehicle:
        base_data = {
            "vehicle_id": vehicle_id,
            "station_id": station_id,
            "status": VehicleStatus.available,
            "rides_since_last_treated": 0,
            "last_treated_date": None
        }

        v_type = {
            "bike": Bicycle(vehicle_type=VehicleType.bike, **base_data),
            "ebike": ElectricBicycle(vehicle_type=VehicleType.ebike, **base_data),
            "scooter": Scooter(vehicle_type=VehicleType.scooter, **base_data)
        }
        return v_type[vehicle_type.lower()]


