"""Review response schemas for the MedCare API layer."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewResponse(BaseModel):
    """Review detail response payload."""

    id: str = Field(..., description="Unique identifier of the review")
    appointment_id: str = Field(..., description="Completed appointment being reviewed")
    patient_id: str = Field(..., description="Patient who submitted the review")
    doctor_id: str = Field(..., description="Doctor who received the review")
    rating: int = Field(..., ge=1, le=5, description="Rating score given by the patient")
    comment: str | None = Field(
        default=None,
        description="Optional written feedback shared by the patient",
    )
    is_hidden: bool = Field(..., description="Whether the review is hidden by admin moderation")
    created_at: datetime = Field(..., description="UTC timestamp when the review was created")

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class ReviewListResponse(BaseModel):
    """Review list response payload."""

    items: list[ReviewResponse] = Field(
        default_factory=list,
        description="Collection of review records",
    )

    model_config = ConfigDict(extra="forbid")

