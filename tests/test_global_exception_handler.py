"""
Integration tests for global exception handling.
Verifies that custom exceptions are properly mapped to HTTP status codes.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from src.main import app
from src.exceptions import ValidationException, NotFoundException, ConflictException


@pytest.mark.asyncio
async def test_validation_exception_returns_400():
    """Test that ValidationException is mapped to 400 Bad Request."""
    with patch("src.controllers.vehicles_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        with patch("src.controllers.vehicles_controller.service.treat_vehicle") as mock_treat:
            mock_treat.side_effect = ValidationException("Vehicle not eligible for treatment")
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/vehicles/V001/treat")
            
            assert response.status_code == 400
            assert response.json()["detail"] == "Vehicle not eligible for treatment"


@pytest.mark.asyncio
async def test_not_found_exception_returns_404():
    """Test that NotFoundException is mapped to 404 Not Found."""
    with patch("src.controllers.vehicles_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        with patch("src.controllers.vehicles_controller.service.get_vehicle_by_id") as mock_get:
            mock_get.return_value = None
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/vehicles/NONEXISTENT")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_conflict_exception_returns_409():
    """Test that ConflictException is mapped to 409 Conflict."""
    with patch("src.controllers.users_controller.get_db") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        with patch("src.controllers.users_controller.service.create_user") as mock_create:
            mock_create.side_effect = ConflictException("User already exists")
            
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/users/register",
                    json={
                        "user_id": "USER001",
                        "first_name": "Test",
                        "last_name": "User",
                        "email": "test@example.com"
                    }
                )
            
            assert response.status_code == 409
            assert response.json()["detail"] == "User already exists"


@pytest.mark.asyncio
async def test_pydantic_validation_error_returns_422():
    """Test that Pydantic validation errors return 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Missing required fields
        response = await client.post("/users/register", json={})
    
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_pydantic_field_validation_returns_422():
    """Test that Pydantic field validation errors return 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Invalid latitude (must be between -90 and 90)
        response = await client.post(
            "/ride/start",
            json={
                "user_id": "USER001",
                "lon": 34.0,
                "lat": 999.0  # Invalid latitude
            }
        )
    
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_multiple_exception_types_in_single_flow():
    """Test that different endpoints handle different exception types correctly."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test 404 - Not Found
        with patch("src.controllers.vehicles_controller.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            with patch("src.controllers.vehicles_controller.service.get_vehicle_by_id") as mock_get:
                mock_get.return_value = None
                
                response = await client.get("/vehicles/NOTFOUND")
                assert response.status_code == 404
        
        # Test 422 - Validation Error
        response = await client.post("/users/register", json={})
        assert response.status_code == 422
        
        # Test 409 - Conflict
        with patch("src.controllers.users_controller.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            with patch("src.controllers.users_controller.service.create_user") as mock_create:
                mock_create.side_effect = ConflictException("User exists")
                
                response = await client.post(
                    "/users/register",
                    json={
                        "user_id": "USER001",
                        "first_name": "Test",
                        "last_name": "User",
                        "email": "test@example.com"
                    }
                )
                assert response.status_code == 409
