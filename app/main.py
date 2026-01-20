from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import config
from app.deps import SessionDep
from app.models import HealthCheck
from app.routers import auth, projects, tasks

app = FastAPI(
    title="Task Management API",
    description="REST API for managing tasks.",
    version="1.0.0",
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


app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)


@app.get(
    "/health",
    tags=["status"],
    summary="Perform a health check",
    response_model=HealthCheck,
)
async def read_health(*, _session: SessionDep) -> HealthCheck:
    return HealthCheck(status="ok")
