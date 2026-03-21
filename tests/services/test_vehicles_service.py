from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock, ANY
from datetime import date, datetime

from src.services.vehicles_service import VehiclesService
from src.repositories.vehicles_repository import VehiclesRepository
from src.repositories.rides_repository import RidesRepository
from src.models.ride import Ride
from src.models.vehicle import VehicleType, VehicleStatus, Vehicle


@pytest.mark.asyncio
async def test_get_vehicle_by_id():
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(return_value=Vehicle(
        vehicle_id="V001",
        station_id=1,
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.available,
        rides_since_last_treated=5,
        last_treated_date=date(2025, 1, 1)
    ))

    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.get_vehicle_by_id(mock_db, "V001")
    
    assert result is not None
    assert isinstance(result, Vehicle)
    assert result.vehicle_id == "V001"
    assert result.vehicle_type == VehicleType.bike
    mock_repo.get_by_id.assert_called_once_with(mock_db, "V001")


@pytest.mark.asyncio
async def test_get_vehicle_by_id_not_found():
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(return_value=None)
    
    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.get_vehicle_by_id(mock_db, "V999")
    
    assert result is None
    mock_repo.get_by_id.assert_called_once_with(mock_db, "V999")


@pytest.mark.asyncio
async def test_treat_vehicle_degraded_with_station():
    """Test treating a degraded vehicle that already has a station."""
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(side_effect=[
        Vehicle(vehicle_id="V001", station_id=1, vehicle_type=VehicleType.bike, status=VehicleStatus.degraded, rides_since_last_treated=10, last_treated_date=date(2025, 1, 1)),
        Vehicle(vehicle_id="V001", station_id=1, vehicle_type=VehicleType.bike, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today())
    ])
    mock_repo.treat_vehicle = AsyncMock(return_value=True)
    
    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.treat_vehicle(mock_db, "V001")
    
    assert result.status == VehicleStatus.available
    assert result.rides_since_last_treated == 0
    mock_repo.treat_vehicle.assert_called_once_with(mock_db, "V001", 1)

@pytest.mark.asyncio
async def test_report_vehicle_degraded():
    """Service should mark a vehicle degraded when reported."""
    mock_repo = Mock(spec=VehiclesRepository)
    mock_rides_repo = Mock(spec=RidesRepository)
    mock_repo.get_by_id = AsyncMock(side_effect=[
        Vehicle(vehicle_id="V005", station_id=1, vehicle_type=VehicleType.bike, status=VehicleStatus.available, rides_since_last_treated=2, last_treated_date=date(2025, 1, 1)),
        Vehicle(vehicle_id="V005", station_id=None, vehicle_type=VehicleType.bike, status=VehicleStatus.degraded, rides_since_last_treated=2, last_treated_date=date(2025, 1, 1))
    ])
    mock_repo.mark_vehicle_degraded_and_detach = AsyncMock(return_value=True)
    mock_rides_repo.get_active_ride_by_vehicle = AsyncMock(return_value=None)

    service = VehiclesService(repository=mock_repo, rides_repository=mock_rides_repo)
    mock_db = Mock()

    result = await service.report_vehicle_degraded(mock_db, "V005")
    assert result.status == VehicleStatus.degraded
    assert result.station_id is None
    mock_repo.mark_vehicle_degraded_and_detach.assert_called_once_with(mock_db, "V005")


@pytest.mark.asyncio
async def test_report_vehicle_degraded_auto_completes_active_ride_with_zero_charge_flag():
    """Service should auto-complete an active ride as degraded when reporting vehicle breakdown."""
    mock_repo = Mock(spec=VehiclesRepository)
    mock_rides_repo = Mock(spec=RidesRepository)

    active_ride = Ride(
        ride_id="RIDE_ACTIVE_1",
        user_id="USER001",
        vehicle_id="V005",
        start_station_id=1,
        end_station_id=None,
        start_time=datetime(2026, 3, 21, 10, 0, 0),
        end_time=None,
        is_degraded_report=False,
    )

    mock_repo.get_by_id = AsyncMock(side_effect=[
        Vehicle(vehicle_id="V005", station_id=None, vehicle_type=VehicleType.bike, status=VehicleStatus.rented, rides_since_last_treated=2, last_treated_date=date(2025, 1, 1)),
        Vehicle(vehicle_id="V005", station_id=None, vehicle_type=VehicleType.bike, status=VehicleStatus.degraded, rides_since_last_treated=2, last_treated_date=date(2025, 1, 1)),
    ])
    mock_repo.mark_vehicle_degraded_and_detach = AsyncMock(return_value=True)
    mock_rides_repo.get_active_ride_by_vehicle = AsyncMock(return_value=active_ride)
    mock_rides_repo.complete_ride = AsyncMock(return_value=True)

    service = VehiclesService(repository=mock_repo, rides_repository=mock_rides_repo)
    mock_db = Mock()

    result = await service.report_vehicle_degraded(mock_db, "V005")

    assert result.status == VehicleStatus.degraded
    assert result.station_id is None
    mock_rides_repo.complete_ride.assert_called_once_with(
        mock_db,
        ride_id="RIDE_ACTIVE_1",
        end_station_id=None,
        end_time=ANY,
        is_degraded_report=True,
    )
    mock_repo.mark_vehicle_degraded_and_detach.assert_called_once_with(mock_db, "V005")


@pytest.mark.asyncio
async def test_report_vehicle_degraded_already_degraded():
    """Service should raise ValueError when vehicle is already degraded."""
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(return_value=Vehicle(
        vehicle_id="V006",
        station_id=1,
        vehicle_type=VehicleType.bike,
        status=VehicleStatus.degraded,
        rides_since_last_treated=2,
        last_treated_date=date(2025, 1, 1)
    ))

    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()

    with pytest.raises(ValueError, match="already marked as degraded"):
        await service.report_vehicle_degraded(mock_db, "V006")

    # Verify that update_vehicle_status was never called
    mock_repo.mark_vehicle_degraded_and_detach.assert_not_called()


@pytest.mark.asyncio
async def test_report_vehicle_degraded_not_found():
    """Service should raise ValueError when vehicle doesn't exist."""
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(return_value=None)

    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()

    with pytest.raises(ValueError, match="not found"):
        await service.report_vehicle_degraded(mock_db, "V999")

@pytest.mark.asyncio
async def test_treat_vehicle_rides_threshold():
    """Test treating a vehicle that reached rides threshold but not degraded."""
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(side_effect=[
        Vehicle(vehicle_id="V002", station_id=2, vehicle_type=VehicleType.scooter, status=VehicleStatus.available, rides_since_last_treated=7, last_treated_date=date(2025, 1, 2)),
        Vehicle(vehicle_id="V002", station_id=2, vehicle_type=VehicleType.scooter, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today())
    ])
    mock_repo.treat_vehicle = AsyncMock(return_value=True)
    
    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.treat_vehicle(mock_db, "V002")
    
    assert result.status == VehicleStatus.available
    assert result.rides_since_last_treated == 0


@pytest.mark.asyncio
async def test_treat_vehicle_not_eligible():
    """Test that treatment fails for non-eligible vehicle."""
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(return_value=Vehicle(
        vehicle_id="V003", station_id=1, vehicle_type=VehicleType.bike, status=VehicleStatus.available, rides_since_last_treated=3, last_treated_date=date(2025, 1, 3)
    ))

    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    with pytest.raises(ValueError, match="not eligible for treatment"):
        await service.treat_vehicle(mock_db, "V003")


@pytest.mark.asyncio
async def test_treat_vehicle_degraded_needs_station():
    """Test that treatment fails for degraded vehicle without station."""
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(return_value=Vehicle(
        vehicle_id="V004", station_id=None, vehicle_type=VehicleType.bike, status=VehicleStatus.degraded, rides_since_last_treated=10, last_treated_date=date(2025, 1, 4)
    ))

    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    with pytest.raises(ValueError, match="Must provide a station_id"):
        await service.treat_vehicle(mock_db, "V004")


@pytest.mark.asyncio
async def test_treat_vehicle_degraded_assign_station():
    """Test treating a degraded vehicle by assigning a station."""
    mock_repo = Mock(spec=VehiclesRepository)
    mock_repo.get_by_id = AsyncMock(side_effect=[
        Vehicle(vehicle_id="V004", station_id=None, vehicle_type=VehicleType.bike, status=VehicleStatus.degraded, rides_since_last_treated=10, last_treated_date=date(2025, 1, 4)),
        Vehicle(vehicle_id="V004", station_id=3, vehicle_type=VehicleType.bike, status=VehicleStatus.available, rides_since_last_treated=0, last_treated_date=date.today())
    ])
    mock_repo.treat_vehicle = AsyncMock(return_value=True)
    
    service = VehiclesService(repository=mock_repo)
    mock_db = Mock()
    
    result = await service.treat_vehicle(mock_db, "V004", station_id=3)
    
    assert result.status == VehicleStatus.available
    assert result.rides_since_last_treated == 0
    assert result.station_id == 3
    mock_repo.treat_vehicle.assert_called_once_with(mock_db, "V004", 3)