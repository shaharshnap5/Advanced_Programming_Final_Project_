from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, patch

from src.models.FleetManager import FleetManager
from src.models.ride import Ride
from src.models.station import Station
from src.models.user import User
from src.models.vehicle import Vehicle, VehicleStatus, VehicleType
from src.services.rides_service import RidesService
from src.services.stations_service import StationsService
from src.services.users_service import UsersService
from src.services.vehicles_service import VehiclesService


class TestRideCompletionFlow:
    """Integration tests for the complete ride end-to-end flow."""

    @pytest.mark.asyncio
    async def test_complete_ride_end_flow(self):
        """Test the entire ride completion flow with mocked database."""
        # Setup mocked services
        mock_stations_service = AsyncMock(spec=StationsService)
        mock_users_service = AsyncMock(spec=UsersService)
        mock_vehicles_service = AsyncMock(spec=VehiclesService)

        # Mock data
        station_data = Station(
            station_id=5,
            name="Downtown Station",
            lat=32.5,
            lon=34.5,
            max_capacity=20,
            vehicles=[],
        )

        vehicle_data = {
            "vehicle_id": "BIKE_001",
            "station_id": 1,
            "vehicle_type": "bike",
            "status": "rented",
            "rides_since_last_treated": 3,
            "last_treated_date": None,
        }

        user_data = {
            "user_id": "USER_ALPHA",
            "payment_token": "tok_visa_123456",
            "current_ride_id": "RIDE_001",
        }

        mock_stations_service.get_nearest_station_with_capacity = AsyncMock(
            return_value=station_data
        )
        mock_vehicles_service.get_vehicle_by_id = AsyncMock(return_value=vehicle_data)
        mock_vehicles_service.dock_vehicle = AsyncMock(return_value=vehicle_data)
        mock_users_service.get_user_by_id = AsyncMock(return_value=user_data)
        mock_users_service.clear_current_ride = AsyncMock(return_value=True)

        service = RidesService(
            stations_service=mock_stations_service,
            users_service=mock_users_service,
            vehicles_service=mock_vehicles_service,
        )

        with patch.object(FleetManager, "_instance", None):
            fm = FleetManager()
            # Add multiple active rides to test correct filtering
            ride1 = Ride(ride_id="RIDE_001", user_id="USER_ALPHA", vehicle_id="BIKE_001")
            ride2 = Ride(ride_id="RIDE_002", user_id="USER_BETA", vehicle_id="SCOOTER_002")
            fm.active_rides["RIDE_001"] = ride1
            fm.active_rides["RIDE_002"] = ride2

            mock_db = Mock()

            result = await service.end_ride(
                mock_db, "RIDE_001", lon=34.5, lat=32.5
            )

            # Verify response
            assert result["end_station_id"] == 5
            assert result["payment_charged"] == 15
            assert result["active_users"] == ["USER_BETA"]  # Only RIDE_002 remains

            # Verify service calls were made correctly
            mock_stations_service.get_nearest_station_with_capacity.assert_called_once_with(
                mock_db, 34.5, 32.5
            )
            mock_vehicles_service.dock_vehicle.assert_called_once_with(
                mock_db, "BIKE_001", 5, 4, "available"
            )
            mock_users_service.get_user_by_id.assert_called_once_with(mock_db, "USER_ALPHA")
            mock_users_service.clear_current_ride.assert_called_once_with(mock_db, "USER_ALPHA")

    @pytest.mark.asyncio
    async def test_ride_end_with_degraded_report(self):
        """Test ride end when user reported vehicle as degraded."""
        mock_stations_service = AsyncMock(spec=StationsService)
        mock_users_service = AsyncMock(spec=UsersService)
        mock_vehicles_service = AsyncMock(spec=VehiclesService)

        station_data = Station(
            station_id=3,
            name="Degraded Station",
            lat=32.3,
            lon=34.3,
            max_capacity=10,
            vehicles=[],
        )
        vehicle_data = {
            "vehicle_id": "SCOOTER_001",
            "station_id": 1,
            "vehicle_type": "scooter",
            "status": "rented",
            "rides_since_last_treated": 8,
            "last_treated_date": None,
        }
        user_data = {
            "user_id": "USER_GAMMA",
            "payment_token": "tok_amex_789",
            "current_ride_id": "RIDE_DEGRADED",
        }

        mock_stations_service.get_nearest_station_with_capacity = AsyncMock(
            return_value=station_data
        )
        mock_vehicles_service.get_vehicle_by_id = AsyncMock(return_value=vehicle_data)
        mock_vehicles_service.dock_vehicle = AsyncMock(return_value=vehicle_data)
        mock_users_service.get_user_by_id = AsyncMock(return_value=user_data)
        mock_users_service.clear_current_ride = AsyncMock(return_value=True)

        service = RidesService(
            stations_service=mock_stations_service,
            users_service=mock_users_service,
            vehicles_service=mock_vehicles_service,
        )

        with patch.object(FleetManager, "_instance", None):
            fm = FleetManager()
            # Ride marked as degraded
            ride = Ride(
                ride_id="RIDE_DEGRADED",
                user_id="USER_GAMMA",
                vehicle_id="SCOOTER_001",
                is_degraded_report=True,
            )
            fm.active_rides["RIDE_DEGRADED"] = ride

            mock_db = Mock()
            result = await service.end_ride(mock_db, "RIDE_DEGRADED", 34.3, 32.3)

            # Degraded rides should not charge
            assert result["payment_charged"] == 0
            assert result["end_station_id"] == 3

    @pytest.mark.asyncio
    async def test_multiple_concurrent_ride_ends(self):
        """Test that ride end correctly handles multiple active rides."""
        mock_stations_service = AsyncMock(spec=StationsService)
        mock_users_service = AsyncMock(spec=UsersService)
        mock_vehicles_service = AsyncMock(spec=VehiclesService)

        station_data = Station(
            station_id=7,
            name="Shared Station",
            lat=32.7,
            lon=34.7,
            max_capacity=10,
            vehicles=[],
        )
        vehicle_data = {
            "vehicle_id": "BIKE_002",
            "station_id": 2,
            "vehicle_type": "bike",
            "status": "rented",
            "rides_since_last_treated": 2,
            "last_treated_date": None,
        }
        user_data = {
            "user_id": "USER_DELTA",
            "payment_token": "tok_mastercard",
            "current_ride_id": "RIDE_003",
        }

        mock_stations_service.get_nearest_station_with_capacity = AsyncMock(
            return_value=station_data
        )
        mock_vehicles_service.get_vehicle_by_id = AsyncMock(return_value=vehicle_data)
        mock_vehicles_service.dock_vehicle = AsyncMock(return_value=vehicle_data)
        mock_users_service.get_user_by_id = AsyncMock(return_value=user_data)
        mock_users_service.clear_current_ride = AsyncMock(return_value=True)

        service = RidesService(
            stations_service=mock_stations_service,
            users_service=mock_users_service,
            vehicles_service=mock_vehicles_service,
        )

        with patch.object(FleetManager, "_instance", None):
            fm = FleetManager()
            # Add 5 active rides
            rides = [
                Ride(ride_id=f"RIDE_{i:03d}", user_id=f"USER_{i:03d}", vehicle_id=f"VEH_{i:03d}")
                for i in range(1, 6)
            ]
            for ride in rides:
                fm.active_rides[ride.ride_id] = ride

            mock_db = Mock()
            result = await service.end_ride(mock_db, "RIDE_003", 34.7, 32.7)

            # After ending RIDE_003, 4 active users should remain
            assert len(result["active_users"]) == 4
            assert "USER_003" not in result["active_users"]
            assert "RIDE_003" not in fm.active_rides

    @pytest.mark.asyncio
    async def test_ride_end_vehicle_degradation_threshold(self):
        """Test vehicle degradation after crossing 10 rides threshold."""
        mock_stations_service = AsyncMock(spec=StationsService)
        mock_users_service = AsyncMock(spec=UsersService)
        mock_vehicles_service = AsyncMock(spec=VehiclesService)

        station_data = Station(
            station_id=10,
            name="Degradation Station",
            lat=32.10,
            lon=34.10,
            max_capacity=10,
            vehicles=[],
        )
        vehicle_data = {
            "vehicle_id": "EBIKE_001",
            "station_id": 5,
            "vehicle_type": "ebike",
            "status": "rented",
            "rides_since_last_treated": 10,  # Just at threshold
            "last_treated_date": None,
        }
        user_data = {
            "user_id": "USER_EPSILON",
            "payment_token": "tok_discover",
            "current_ride_id": "RIDE_THRESHOLD",
        }

        mock_stations_service.get_nearest_station_with_capacity = AsyncMock(
            return_value=station_data
        )
        mock_vehicles_service.get_vehicle_by_id = AsyncMock(return_value=vehicle_data)
        mock_vehicles_service.dock_vehicle = AsyncMock(return_value=vehicle_data)
        mock_users_service.get_user_by_id = AsyncMock(return_value=user_data)
        mock_users_service.clear_current_ride = AsyncMock(return_value=True)

        service = RidesService(
            stations_service=mock_stations_service,
            users_service=mock_users_service,
            vehicles_service=mock_vehicles_service,
        )

        with patch.object(FleetManager, "_instance", None):
            fm = FleetManager()
            ride = Ride(
                ride_id="RIDE_THRESHOLD",
                user_id="USER_EPSILON",
                vehicle_id="EBIKE_001",
            )
            fm.active_rides["RIDE_THRESHOLD"] = ride

            mock_db = Mock()
            result = await service.end_ride(mock_db, "RIDE_THRESHOLD", 34.10, 32.10)

            # Verify that dock_vehicle was called with status='degraded'
            # because new_rides (10 + 1 = 11) > 10
            call_args = mock_vehicles_service.dock_vehicle.call_args
            assert call_args[0][4] == "degraded"
