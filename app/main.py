import time

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.deps import SessionDep
from app.api.main import api_router
from app.core.config import settings

app = FastAPI(
    title="Task Management API",
    description="A high-performance REST-full API for managing tasks.",
    version="1.0.0",
)

# Set all CORS enabled origins while avoiding allow_origins=["*"] which permits
# any domain and disables credential support. max_age reduces preflight request
# overhead for frequently accessed endpoints.
app.add_middleware(
    CORSMiddleware,  # ty:ignore[invalid-argument-type]
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    expose_headers=["X-Process-Time"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

app.include_router(api_router, prefix=settings.api_v1_str)


@app.get("/health", tags=["status"], status_code=status.HTTP_200_OK)
async def read_health_check(_session: SessionDep) -> JSONResponse:
    return JSONResponse(content={"status": "healthy", "timestamp": time.time()})
