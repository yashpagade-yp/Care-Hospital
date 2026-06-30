"""Review request schemas for the MedCare API layer."""

from pydantic import BaseModel, ConfigDict, Field


class CreateReviewRequest(BaseModel):
    """Patient review submission payload for completed appointments."""

    appointment_id: str = Field(..., description="Completed appointment being reviewed")
    rating: int = Field(..., ge=1, le=5, description="Rating given by the patient")
    comment: str | None = Field(
        default=None,
        description="Optional written feedback for the doctor",
    )

    model_config = ConfigDict(extra="forbid")


class HideReviewRequest(BaseModel):
    """Admin moderation payload used to hide or unhide a review."""

    is_hidden: bool = Field(..., description="Whether the review should be hidden from patient-facing views")

    model_config = ConfigDict(extra="forbid")

