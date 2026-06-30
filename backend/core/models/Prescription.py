"""Prescription persistence model for the MedCare platform.

This model stores structured consultation output created by doctors for a
specific appointment and visible only to the related patient and doctor.
"""

from datetime import datetime, timezone
from typing import Optional

from odmantic import Field, Model


class Prescription(Model):
    """Represents a prescription record created for an appointment.

    The model stores medicines and consultation notes written by the doctor
    after the patient visit.
    """

    appointment_id: str = Field(..., description="Identifier of the linked appointment")
    doctor_id: str = Field(..., description="Identifier of the doctor user")
    patient_id: str = Field(..., description="Identifier of the patient user")
    medicines: list[str] = Field(
        default_factory=list,
        description="Structured list of prescribed medicines",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional consultation notes written by the doctor",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the prescription was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the prescription was last updated",
    )

    model_config = {
        "collection": "prescriptions",
        "extra": "forbid",
    }
