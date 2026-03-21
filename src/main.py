from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.controllers.register_controller import router as register_router
from src.controllers.rides_controller import router as rides_router
from src.controllers.stations_controller import router as stations_router
from src.controllers.vehicles_controller import router as vehicles_router
from src.controllers.vehicle_controller import router as vehicle_router
from src.controllers.users_controller import router as users_router
from src.exceptions import ConflictException, NotFoundException, ValidationException

app = FastAPI(title="Advanced Programming Final Project")
app.include_router(register_router)
app.include_router(rides_router)
app.include_router(stations_router)
app.include_router(vehicles_router)
app.include_router(vehicle_router)
app.include_router(users_router)


@app.exception_handler(ValidationException)
async def handle_validation_exception(_: Request, exc: ValidationException) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(NotFoundException)
async def handle_not_found_exception(_: Request, exc: NotFoundException) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictException)
async def handle_conflict_exception(_: Request, exc: ConflictException) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.errors()})


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Server is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
