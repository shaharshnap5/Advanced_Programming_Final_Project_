from fastapi import FastAPI

from src.controllers.stations_controller import router as stations_router
from src.controllers.vehicles_controller import router as vehicles_router

app = FastAPI(title="Advanced Programming Final Project")
app.include_router(stations_router)
app.include_router(vehicles_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Server is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
