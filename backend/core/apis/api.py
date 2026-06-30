"""FastAPI application wiring for the MedCare backend.

This module creates the shared FastAPI app, configures startup and shutdown
database hooks, and exposes lightweight health endpoints while the route layer
is being built out.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.commons.logger import logger
from backend.core.database.database import close_mongo_connection, connect_to_mongo

logging = logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Manage application startup and shutdown resources.

    The lifespan currently validates the MongoDB connection on startup and
    closes the shared client when the application stops.
    """

    logging.info("Starting MedCare API lifespan")
    await connect_to_mongo()
    try:
        yield
    finally:
        await close_mongo_connection()
        logging.info("Stopped MedCare API lifespan")


app = FastAPI(
    title="MedCare Backend API",
    description="Backend API for the MedCare hospital management platform.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    """Return a simple welcome payload for the API root.

    This endpoint confirms that the FastAPI application is reachable and that
    the base application wiring is working.

    Returns:
        dict[str, str]: Welcome payload for the API root.
    """

    logging.info("Calling GET / endpoint")
    return {"message": "Welcome to the MedCare Backend API"}


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Return a health status payload for infrastructure checks.

    Returns:
        dict[str, str]: Simple status payload indicating API availability.
    """

    logging.info("Calling GET /health endpoint")
    return {"status": "ok"}
