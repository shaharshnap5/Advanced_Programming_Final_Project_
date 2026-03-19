from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.controllers.stations_controller import router as stations_router
from src.controllers.vehicles_controller import router as vehicles_router
from src.controllers.users_controller import router as users_router
from src.controllers.ride_controller import router as ride_router
from src.exceptions import ValidationException, NotFoundException, ConflictException

app = FastAPI(title="Advanced Programming Final Project")


# Custom exception handlers for business logic errors
@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handle validation exceptions and return 400 Bad Request."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message}
    )


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """Handle not found exceptions and return 404 Not Found."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message}
    )


@app.exception_handler(ConflictException)
async def conflict_exception_handler(request: Request, exc: ConflictException):
    """Handle conflict exceptions and return 409 Conflict."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message}
    )


# Pydantic validation error handler
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors and return 400 Bad Request."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Invalid input", "errors": exc.errors()}
    )


# Generic 404 Handler for unimplemented routes
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: StarletteHTTPException):
    """Return 404 for requests to routes that don't exist."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Route not found"}
    )


# Generic 500/502 Handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return 502 Bad Gateway."""
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "Internal server error"}
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
