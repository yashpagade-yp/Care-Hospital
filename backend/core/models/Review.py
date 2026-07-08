"""Review persistence model for the MedCare platform.

This model stores patient feedback for completed appointments and supports
admin moderation through a hidden flag.
"""

from datetime import datetime, timezone
from typing import Optional

from odmantic import Field, Model


class Review(Model):
    """Represents a patient review submitted for an appointment.

    Each review is linked to one appointment and can be hidden by the admin
    without deleting the original feedback record.
    """

    appointment_id: str = Field(
        ...,
        unique=True,
        description="Identifier of the appointment being reviewed",
    )
    patient_id: str = Field(..., description="Identifier of the patient user")
    doctor_id: str = Field(..., description="Identifier of the doctor user")
    rating: int = Field(..., ge=1, le=5, description="Patient rating for the doctor")
    comment: Optional[str] = Field(
        default=None,
        description="Optional written feedback submitted by the patient",
    )
    is_hidden: bool = Field(
        default=False,
        description="Indicates whether the review has been hidden by an admin",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the review was created",
    )

    model_config = {
        "collection": "reviews",
        "extra": "forbid",
    }
