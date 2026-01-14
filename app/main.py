from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import config
from app.core.db import create_db_and_tables
from app.deps import SessionDep
from app.routers import tasks


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Task Management API",
    description="REST API for managing tasks",
    version="1.0.0",
    lifespan=lifespan,
)

# Set all CORS enabled origins
if config.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,  # ty:ignore[invalid-argument-type]
        allow_origins=config.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(tasks.router)


@dataclass
class HealthCheck:
    status: str


@app.get(
    "/health",
    tags=["status"],
    summary="Perform a Health Check",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
async def read_health(*, _session: SessionDep) -> HealthCheck:
    return HealthCheck(status="ok")
