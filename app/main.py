import time

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.deps import SessionDep
from app.api.main import api_router
from app.core.config import settings
from app.core.limiter import limiter

app = FastAPI(
    title="Task Management API",
    description="A high-performance REST-full API for managing tasks.",
    version="1.0.0",
)

# Setup rate limiter
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,  # pyrefly:ignore[bad-argument-type]
)
app.add_middleware(SlowAPIMiddleware)


# Set all CORS enabled origins while avoiding allow_origins=["*"] which permits
# any domain and disables credential support. max_age reduces preflight request
# overhead for frequently accessed endpoints.
app.add_middleware(
    CORSMiddleware,
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
