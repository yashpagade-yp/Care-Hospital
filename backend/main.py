"""Runtime entrypoint for the MedCare backend application.

This module exposes the FastAPI app for ASGI servers and starts Uvicorn when
executed directly for local development.
"""

from __future__ import annotations

import os

import uvicorn
from dotenv import load_dotenv

from backend.commons.logger import logger
from backend.core.apis.api import app

load_dotenv()

logging = logger(__name__)


if __name__ == "__main__":
    # Local development entrypoint for the FastAPI application.
    logging.info("Starting MedCare backend via backend.main")
    uvicorn.run(
        "backend.main:app",
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "8000")),
        reload=os.getenv("APP_RELOAD", "false").lower() == "true",
    )
