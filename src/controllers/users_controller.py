from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from aiosqlite import Connection

from src.db import get_db
from src.models.user import UserCreate, UserRegisterResponse
from src.services.users_service import UsersService

router = APIRouter(prefix="/users", tags=["users"])
service = UsersService()


@router.post("/register", response_model=UserRegisterResponse)
async def create_user(
    request: Request, db: Connection = Depends(get_db)
) -> JSONResponse:
    """Register a new user or login existing user with provided user_id.

    If the user does not exist, create a new account with status 201.
    If the user exists, return the existing user data with status 200.
    """
    try:
        payload = await request.json()
    except Exception:  # pragma: no cover
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        data = UserCreate.model_validate(payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())

    try:
        user, is_existing = await service.create_or_login_user(
            db,
            data.user_id,
            data.first_name,
            data.last_name,
            data.email,
        )
    except ValueError as err:
        raise HTTPException(status_code=409, detail=str(err))

    response_data = UserRegisterResponse(
        message=(
            "User already exists, details:"
            if is_existing
            else "User created successfully"
        ),
        user=user,
    )

    status_code = status.HTTP_200_OK if is_existing else status.HTTP_201_CREATED

    return JSONResponse(status_code=status_code, content=response_data.model_dump())
