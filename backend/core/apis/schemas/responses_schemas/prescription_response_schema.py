"""Prescription response schemas for the MedCare API layer."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PrescriptionResponse(BaseModel):
    """Prescription detail response payload."""

    id: str = Field(..., description="Unique identifier of the prescription")
    appointment_id: str = Field(..., description="Appointment linked to the prescription")
    doctor_id: str = Field(..., description="Doctor who created the prescription")
    patient_id: str = Field(..., description="Patient who can view the prescription")
    medicines: list[str] = Field(
        default_factory=list,
        description="Structured list of prescribed medicines",
    )
    notes: str | None = Field(
        default=None,
        description="Additional consultation notes included in the prescription",
    )
    created_at: datetime = Field(..., description="UTC timestamp when the prescription was created")
    updated_at: datetime = Field(..., description="UTC timestamp when the prescription was updated")

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class PrescriptionListResponse(BaseModel):
    """Prescription list response payload."""

    items: list[PrescriptionResponse] = Field(
        default_factory=list,
        description="Collection of prescription records",
    )

    model_config = ConfigDict(extra="forbid")

