from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.cors import setup_cors
from app.core.db import create_db_and_tables
from app.core.logging import logger  # noqa: F401
from app.routers import tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Task Management API",
    description="REST API for managing tasks",
    version="1.0.0",
    lifespan=lifespan,
)

setup_cors(app)

app.include_router(tasks.router)


@app.get(
    "/health",
    tags=["status"],
    summary="Perform a Health Check",
)
async def read_health():
    return {status: "OK"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred", "path": request.url.path},
    )


@app.exception_handler(HTTPException)
async def enhanced_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": exc.headers.get("X-Error-Code") if exc.headers else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
