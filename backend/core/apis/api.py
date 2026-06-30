"""FastAPI application wiring for the MedCare backend.

This module creates the shared FastAPI app, configures startup and shutdown
database hooks, and exposes lightweight health endpoints while the route layer
is being built out.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.commons.logger import logger
from backend.core.apis.routers.auth_router import auth_router
from backend.core.apis.routers.appointment_router import appointment_router
from backend.core.apis.routers.availability_router import availability_router
from backend.core.apis.routers.dashboard_router import dashboard_router
from backend.core.apis.routers.invitation_router import invitation_router
from backend.core.apis.routers.payment_router import payment_router
from backend.core.apis.routers.prescription_router import prescription_router
from backend.core.apis.routers.review_router import review_router
from backend.core.apis.routers.user_router import user_router
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

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(invitation_router)
app.include_router(availability_router)
app.include_router(appointment_router)
app.include_router(payment_router)
app.include_router(prescription_router)
app.include_router(review_router)
app.include_router(dashboard_router)


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
