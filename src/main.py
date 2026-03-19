from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.controllers.stations_controller import router as stations_router
from src.controllers.vehicles_controller import router as vehicles_router
from src.controllers.users_controller import router as users_router
from src.controllers.ride_controller import router as ride_router

app = FastAPI(title="Advanced Programming Final Project")


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
