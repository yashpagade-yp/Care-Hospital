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
    patient_name: Optional[str] = Field(
        default=None,
        description="Patient name snapshot copied from the linked appointment",
    )
    patient_phone: Optional[str] = Field(
        default=None,
        description="Patient phone snapshot copied from the linked appointment",
    )
    patient_age: Optional[int] = Field(
        default=None,
        ge=0,
        le=120,
        description="Patient age snapshot copied from the linked appointment",
    )
    patient_gender: Optional[str] = Field(
        default=None,
        description="Patient gender snapshot copied from the linked appointment",
    )
    patient_blood_group: Optional[str] = Field(
        default=None,
        description="Patient blood group snapshot copied from the linked appointment",
    )
    visit_reason: Optional[str] = Field(
        default=None,
        description="Visit reason snapshot copied from the linked appointment",
    )
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
