from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.controllers.stations_controller import router as stations_router
from src.controllers.vehicles_controller import router as vehicles_router
from src.controllers.users_controller import router as users_router
from src.controllers.ride_controller import router as ride_router
from src.exceptions import ValidationException, NotFoundException, ConflictException

app = FastAPI(title="Advanced Programming Final Project")


# Global Exception Handlers
@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handle ValidationException and return 400 Bad Request."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message}
    )


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """Handle NotFoundException and return 404 Not Found."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message}
    )


@app.exception_handler(ConflictException)
async def conflict_exception_handler(request: Request, exc: ConflictException):
    """Handle ConflictException and return 409 Conflict."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message}
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic ValidationError and return 400 Bad Request."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.errors()}
    )


app.include_router(stations_router)
app.include_router(vehicles_router)
app.include_router(users_router)
app.include_router(ride_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Server is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
