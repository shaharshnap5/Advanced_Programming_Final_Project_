from fastapi import FastAPI

from src.controllers.stations_controller import router as stations_router
from src.controllers.vehicles_controller import router as vehicles_router
from src.controllers.users_controller import router as users_router
from src.controllers.ride_controller import router as ride_router

app = FastAPI(title="Advanced Programming Final Project")
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
