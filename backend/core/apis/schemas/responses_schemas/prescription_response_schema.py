"""Prescription response schemas for the MedCare API layer."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PrescriptionResponse(BaseModel):
    """Prescription detail response payload."""

    id: str = Field(..., description="Unique identifier of the prescription")
    appointment_id: str = Field(..., description="Appointment linked to the prescription")
    doctor_id: str = Field(..., description="Doctor who created the prescription")
    doctor_name: str | None = Field(
        default=None,
        description="Doctor display name shown as the treating physician",
    )
    patient_id: str = Field(..., description="Patient who can view the prescription")
    patient_name: str | None = Field(default=None, description="Patient display name shown with the prescription")
    patient_phone: str | None = Field(default=None, description="Patient phone snapshot copied to the prescription")
    patient_age: int | None = Field(default=None, description="Patient age snapshot copied to the prescription")
    patient_gender: str | None = Field(default=None, description="Patient gender snapshot copied to the prescription")
    patient_blood_group: str | None = Field(
        default=None,
        description="Patient blood group snapshot copied to the prescription",
    )
    visit_reason: str | None = Field(
        default=None,
        description="Consultation reason copied from the appointment",
    )
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

