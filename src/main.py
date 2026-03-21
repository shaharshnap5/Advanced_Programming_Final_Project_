from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.controllers.stations_controller import router as stations_router
from src.controllers.vehicles_controller import router as vehicles_router
from src.controllers.users_controller import router as users_router
from src.controllers.rides_controller import router as ride_router

app = FastAPI(title="Advanced Programming Final Project")


# Global exception handler for 404 errors (non-existent routes)
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: StarletteHTTPException):
    # Check if this is a route that doesn't exist vs a resource not found
    # If detail is "Not Found", it means the route doesn't exist
    # If detail is something else (e.g., "Station not found"), it's from application logic
    if exc.detail == "Not Found":
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": f"Route '{request.url.path}' does not exist",
            },
        )
    # Otherwise preserve the original detail message from the application
    return JSONResponse(status_code=404, content={"detail": exc.detail})


# Global exception handler for unhandled exceptions (500 errors)
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
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
