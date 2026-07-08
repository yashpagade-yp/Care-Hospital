"""Common response schemas for the MedCare API layer."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MessageResponse(BaseModel):
    """Simple message response payload."""

    message: str = Field(..., description="Human-readable success or information message")

    model_config = ConfigDict(extra="forbid")


# Alias used by admin endpoints that return a plain confirmation message.
CommonMessageResponse = MessageResponse


class ErrorResponse(BaseModel):
    """Standard error payload returned by API endpoints."""

    message: str = Field(..., description="High-level error message")
    details: Any | None = Field(
        default=None,
        description="Optional structured details for the error context",
    )

    model_config = ConfigDict(extra="forbid")


class PaginationMetaResponse(BaseModel):
    """Pagination metadata payload for list responses."""

    total: int = Field(..., ge=0, description="Total number of available records")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items returned per page")

    model_config = ConfigDict(extra="forbid")

