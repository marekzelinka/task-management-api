from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import config


def setup_cors(app: FastAPI) -> None:
    """Set all CORS enabled origins."""
    if config.all_cors_origins:
        app.add_middleware(
            CORSMiddleware,  # ty:ignore[invalid-argument-type]
            allow_origins=config.all_cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
