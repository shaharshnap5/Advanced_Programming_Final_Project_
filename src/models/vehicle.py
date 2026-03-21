from __future__ import annotations
from pydantic import BaseModel
import datetime
from enum import Enum
from typing import Any, Mapping


class VehicleType(str, Enum):
    bicycle = "bicycle"
    electric_bicycle = "electric_bicycle"
    scooter = "scooter"


class VehicleStatus(str, Enum):
    available = "available"
    rented = "rented"
    degraded = "degraded"


class Vehicle(BaseModel):
    vehicle_id: str
    station_id: int | None
    vehicle_type: VehicleType
    status: VehicleStatus
    rides_since_last_treated: int
    last_treated_date: datetime.date | None
    battery: int | None = None

    @property
    def battery_level(self) -> int | None:
        """Backward-compatible alias for older tests and callers."""
        return self.battery

    @battery_level.setter
    def battery_level(self, value: int | None) -> None:
        self.battery = value

    def can_rent(self) -> bool:
        return (
            self.status == VehicleStatus.available
            and self.rides_since_last_treated <= 10
        )

    def rent(self):
        """Rents a vehicle if it is currently eligible."""
        if self.can_rent():
            self.status = VehicleStatus.rented
            self.station_id = None
        else:
            raise Exception("Vehicle is not available for rent")

    def end_active_ride(self):
        """Completes an active ride and updates per-ride counters."""
        self.rides_since_last_treated += 1

    def return_vehicle(self, station_id: int):
        """Returns the vehicle to a station and updates its status.

        Degradation occurs only after more than 10 rides since last treatment.
        """
        self.end_active_ride()
        self.station_id = station_id
        if self.rides_since_last_treated > 10:
            # once the ride count exceeds 10, vehicle becomes degraded
            self.status = VehicleStatus.degraded
        else:
            self.status = VehicleStatus.available

    def report_degraded(self):
        self.status = VehicleStatus.degraded

    def treat(self):
        """Treats a vehicle by resetting maintenance related fields."""
        self.status = VehicleStatus.available
        self.rides_since_last_treated = 0
        self.last_treated_date = datetime.date.today()


class ElectricVehicle(Vehicle):
    battery: int = 100

    def can_rent(self) -> bool:
        return super().can_rent() and self.battery is not None and self.battery >= 14

    def treat(self):
        """Treats and fully recharges the electric vehicle."""
        super().treat()
        self.battery = 100

    def rent(self):
        """Rents the electric vehicle only when it has enough battery for one full ride."""
        if not self.can_rent():
            raise Exception("Electric vehicle is not available for rent")
        self.status = VehicleStatus.rented
        self.station_id = None

    def end_active_ride(self):
        """Completes an electric ride and drains battery by 14%."""
        super().end_active_ride()
        self.battery = max(0, (self.battery or 0) - 14)

    def charge(self):
        """Charges the electric vehicle's battery to full if it's available."""

        if self.status == VehicleStatus.available:
            self.battery = 100
        else:
            raise Exception("Cannot charge a vehicle that is not available")


class Bicycle(Vehicle):
    """Represents a standard bicycle vehicle."""

    vehicle_type: VehicleType = VehicleType.bicycle


class ElectricBicycle(ElectricVehicle):
    """Represents an electric bicycle vehicle."""

    vehicle_type: VehicleType = VehicleType.electric_bicycle
    battery: int = 100


class Scooter(ElectricVehicle):
    vehicle_type: VehicleType = VehicleType.scooter
    battery: int = 100


class VehicleFactory:
    @staticmethod
    def create_vehicle(
        vehicle_id: str, vehicle_type: str, station_id: int | None = None
    ) -> Vehicle:
        base_data = {
            "vehicle_id": vehicle_id,
            "station_id": station_id,
            "status": VehicleStatus.available,
            "rides_since_last_treated": 0,
            "last_treated_date": None,
        }

        v_type = {
            "bicycle": Bicycle(vehicle_type=VehicleType.bicycle, **base_data),
            "electric_bicycle": ElectricBicycle(
                vehicle_type=VehicleType.electric_bicycle, **base_data
            ),
            "scooter": Scooter(vehicle_type=VehicleType.scooter, **base_data),
        }
        return v_type[vehicle_type.lower()]

    @staticmethod
    def from_row(row: Mapping[str, Any]) -> Vehicle:
        """Creates the correct polymorphic vehicle subtype from a DB row."""
        payload = dict(row)
        type_value = payload.get("vehicle_type")

        if (
            type_value
            in {VehicleType.electric_bicycle.value, VehicleType.scooter.value}
            and payload.get("battery") is None
        ):
            payload["battery"] = 100

        constructor = {
            VehicleType.bicycle.value: Bicycle,
            VehicleType.electric_bicycle.value: ElectricBicycle,
            VehicleType.scooter.value: Scooter,
        }.get(type_value, Vehicle)

        return constructor(**payload)
